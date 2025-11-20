import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging

# Cấu hình logging để debug nếu cần
logging.basicConfig(level=logging.INFO)

def fetch_dien_toan(total_days):
    """Lấy kết quả Điện Toán 123"""
    try:
        url = f"https://ketqua04.net/so-ket-qua-dien-toan-123/{total_days}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        divs = soup.find_all("div", class_="result_div", id="result_123")
        data = []
        for div in divs[:total_days]:
            ds = div.find("span", id="result_date")
            date = ds.text.strip() if ds else ""
            tbl = div.find("table", id="result_tab_123")
            if tbl:
                row = tbl.find("tbody").find("tr")
                cells = row.find_all("td") if row else []
                if len(cells) == 3:
                    nums = [c.text.strip() for c in cells]
                    data.append({"date": date, "numbers": nums})
        return data
    except Exception as e:
        logging.error(f"Lỗi Điện Toán: {e}")
        return []

def fetch_than_tai(total_days):
    """Lấy kết quả Thần Tài"""
    try:
        url = f"https://ketqua04.net/so-ket-qua-than-tai/{total_days}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        divs = soup.find_all("div", class_="result_div", id="result_tt4")
        data = []
        for div in divs[:total_days]:
            ds = div.find("span", id="result_date")
            date = ds.text.strip() if ds else ""
            tbl = div.find("table", id="result_tab_tt4")
            if tbl:
                cell = tbl.find("td", id="rs_0_0")
                num = cell.text.strip() if cell else ""
                if len(num) == 4:
                    data.append({"date": date, "number": num})
        return data
    except Exception as e:
        logging.error(f"Lỗi Thần Tài: {e}")
        return []

def fetch_phoi_cau_xsmb(total_days, dien_toan_data_ref=None):
    """Lấy kết quả XSMB (GĐB)"""
    try:
        url = "https://congcuxoso.com/MienBac/DacBiet/PhoiCauDacBiet/PhoiCauTuan5So.aspx"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        tbl = soup.find("table", id="MainContent_dgv")
        if not tbl: return []
        
        rows = tbl.find_all("tr")[1:] # Bỏ header
        nums = []
        for row in reversed(rows):
            # Web này sắp xếp ngược, nên duyệt reversed
            cells = row.find_all("td")
            for cell in reversed(cells):
                t = cell.text.strip()
                if t and t not in ("-----", "\xa0"):
                    nums.append(t.zfill(5))
        
        data = []
        limit = min(len(nums), total_days)
        
        # Ghép ngày từ dữ liệu điện toán (vì web phôi cầu không có ngày rõ ràng)
        if dien_toan_data_ref:
             limit = min(limit, len(dien_toan_data_ref))
             for i in range(limit):
                 data.append({"date": dien_toan_data_ref[i]["date"], "number": nums[i]})
        else:
            # Fallback nếu không có dữ liệu điện toán
            current_date = datetime.now()
            for i in range(limit):
                date_str = (current_date - timedelta(days=i)).strftime("Ngày %d/%m/%Y")
                data.append({"date": date_str, "number": nums[i]})
        return data
    except Exception as e:
        logging.error(f"Lỗi XSMB: {e}")
        return []

def fetch_giai_nhat(total_days, dien_toan_data_ref=None):
    """Lấy kết quả Giải Nhất"""
    try:
        url = "https://congcuxoso.com/MienBac/GiaiNhat/PhoiCauGiaiNhat/PhoiCauTuan5So.aspx"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        tbl = soup.find("table", id="MainContent_dgv")
        if not tbl: return []
        
        rows = tbl.find_all("tr")[1:]
        nums = []
        for row in reversed(rows):
            cells = row.find_all("td")
            for cell in reversed(cells):
                t = cell.text.strip()
                if t and t not in ("-----", "\xa0"):
                    nums.append(t.zfill(5))
                    
        data = []
        limit = min(len(nums), total_days)
        if dien_toan_data_ref:
             limit = min(limit, len(dien_toan_data_ref))
             for i in range(limit):
                 data.append({"date": dien_toan_data_ref[i]["date"], "number": nums[i]})
        else:
            current_date = datetime.now()
            for i in range(limit):
                date_str = (current_date - timedelta(days=i)).strftime("Ngày %d/%m/%Y")
                data.append({"date": date_str, "number": nums[i]})
        return data
    except Exception as e:
        logging.error(f"Lỗi Giải Nhất: {e}")
        return []