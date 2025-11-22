import requests
from bs4 import BeautifulSoup
import concurrent.futures
import logging

logging.basicConfig(level=logging.INFO)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

def fetch_url(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception:
        return None

def fetch_dien_toan(total_days):
    soup = fetch_url(f"https://ketqua04.net/so-ket-qua-dien-toan-123/{total_days}")
    data = []
    if soup:
        divs = soup.find_all("div", class_="result_div", id="result_123")
        for div in divs[:total_days]:
            ds = div.find("span", id="result_date")
            date = ds.text.strip() if ds else ""
            tbl = div.find("table", id="result_tab_123")
            if tbl:
                row = tbl.find("tbody").find("tr")
                cells = row.find_all("td") if row else []
                if len(cells) == 3:
                    nums = [c.text.strip() for c in cells]
                    data.append({"date": date, "dt_numbers": nums})
    return data

def fetch_than_tai(total_days):
    soup = fetch_url(f"https://ketqua04.net/so-ket-qua-than-tai/{total_days}")
    data = []
    if soup:
        divs = soup.find_all("div", class_="result_div", id="result_tt4")
        for div in divs[:total_days]:
            ds = div.find("span", id="result_date")
            date = ds.text.strip() if ds else ""
            tbl = div.find("table", id="result_tab_tt4")
            if tbl:
                cell = tbl.find("td", id="rs_0_0")
                num = cell.text.strip() if cell else ""
                if len(num) == 4:
                    data.append({"date": date, "tt_number": num})
    return data

def _parse_congcuxoso(url, total_days):
    soup = fetch_url(url)
    nums = []
    if soup:
        tbl = soup.find("table", id="MainContent_dgv")
        if tbl:
            rows = tbl.find_all("tr")[1:]
            for row in reversed(rows):
                cells = row.find_all("td")
                for cell in reversed(cells):
                    t = cell.text.strip()
                    if t and t not in ("-----", "\xa0"):
                        nums.append(t.zfill(5))
    return nums[:total_days]

def fetch_xsmb_group(total_days):
    """Hàm tải song song XSMB và G1"""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        f1 = executor.submit(_parse_congcuxoso, "https://congcuxoso.com/MienBac/DacBiet/PhoiCauDacBiet/PhoiCauTuan5So.aspx", total_days)
        f2 = executor.submit(_parse_congcuxoso, "https://congcuxoso.com/MienBac/GiaiNhat/PhoiCauGiaiNhat/PhoiCauTuan5So.aspx", total_days)
        return f1.result(), f2.result()
