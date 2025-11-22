import requests
import concurrent.futures
from bs4 import BeautifulSoup
import logging
import time
from typing import List, Dict, Tuple

logging.basicConfig(level=logging.INFO)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

def fetch_url(url: str, max_retries: int = 3) -> BeautifulSoup:
    """
    Fetch URL with retry logic and better error handling.
    
    Args:
        url: URL to fetch
        max_retries: Maximum number of retry attempts
        
    Returns:
        BeautifulSoup object or None if failed
    """
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except requests.exceptions.Timeout:
            logging.warning(f"Timeout loading {url}, attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait before retry
        except requests.exceptions.RequestException as e:
            logging.error(f"Error loading {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                return None
    return None

def fetch_dien_toan(total_days: int) -> List[Dict]:
    """Fetch Điện Toán 123 data with validation."""
    soup = fetch_url(f"https://ketqua04.net/so-ket-qua-dien-toan-123/{total_days}")
    data = []
    
    if not soup:
        logging.error("Failed to fetch Điện Toán data")
        return data
        
    try:
        divs = soup.find_all("div", class_="result_div", id="result_123")
        for div in divs[:total_days]:
            ds = div.find("span", id="result_date")
            date = ds.text.strip() if ds else ""
            
            if not date:
                continue
                
            tbl = div.find("table", id="result_tab_123")
            if tbl:
                row = tbl.find("tbody").find("tr")
                cells = row.find_all("td") if row else []
                if len(cells) == 3:
                    nums = [c.text.strip() for c in cells]
                    # Validate numbers
                    if all(n.isdigit() for n in nums):
                        data.append({"date": date, "dt_numbers": nums})
    except Exception as e:
        logging.error(f"Error parsing Điện Toán data: {e}")
    
    return data

def fetch_than_tai(total_days: int) -> List[Dict]:
    """Fetch Thần Tài data with validation."""
    soup = fetch_url(f"https://ketqua04.net/so-ket-qua-than-tai/{total_days}")
    data = []
    
    if not soup:
        logging.error("Failed to fetch Thần Tài data")
        return data
        
    try:
        divs = soup.find_all("div", class_="result_div", id="result_tt4")
        for div in divs[:total_days]:
            ds = div.find("span", id="result_date")
            date = ds.text.strip() if ds else ""
            
            if not date:
                continue
                
            tbl = div.find("table", id="result_tab_tt4")
            if tbl:
                cell = tbl.find("td", id="rs_0_0")
                num = cell.text.strip() if cell else ""
                # Validate: should be 4 digits
                if num.isdigit() and len(num) == 4:
                    data.append({"date": date, "tt_number": num})
    except Exception as e:
        logging.error(f"Error parsing Thần Tài data: {e}")
    
    return data

def _parse_congcuxoso(url: str, total_days: int) -> List[str]:
    """Helper function to parse data from congcuxoso with validation."""
    soup = fetch_url(url)
    nums = []
    
    if not soup:
        logging.error(f"Failed to fetch from {url}")
        return nums
        
    try:
        tbl = soup.find("table", id="MainContent_dgv")
        if tbl:
            rows = tbl.find_all("tr")[1:]  # Skip header
            for row in reversed(rows):
                cells = row.find_all("td")
                for cell in reversed(cells):
                    t = cell.text.strip()
                    # Validate and clean data
                    if t and t not in ("-----", "\xa0") and t.replace(" ", "").isdigit():
                        clean_num = t.replace(" ", "").zfill(5)
                        nums.append(clean_num)
    except Exception as e:
        logging.error(f"Error parsing congcuxoso data: {e}")
    
    return nums[:total_days]

def fetch_xsmb_group(total_days: int) -> Tuple[List[str], List[str]]:
    """
    Fetch both ĐB and G1 in parallel for better performance.
    
    Returns:
        Tuple of (ĐB numbers, G1 numbers)
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        f1 = executor.submit(_parse_congcuxoso, 
                            "https://congcuxoso.com/MienBac/DacBiet/PhoiCauDacBiet/PhoiCauTuan5So.aspx", 
                            total_days)
        f2 = executor.submit(_parse_congcuxoso, 
                            "https://congcuxoso.com/MienBac/GiaiNhat/PhoiCauGiaiNhat/PhoiCauTuan5So.aspx", 
                            total_days)
        return f1.result(), f2.result()
