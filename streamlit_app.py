"""
SIÊU GÀ APP - Streamlit Version
Ứng dụng phân tích xổ số Miền Bắc
Author: TRUNGND2025
"""

import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from collections import Counter
import re
from io import StringIO

# ============ CONFIG ============
st.set_page_config(
    page_title="SIÊU GÀ APP",
    page_icon="🐔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ CONSTANTS ============
TOTAL_DAYS = 100
NUM_DAYS = 50

BO_DICT = {
    "00": ["00","55","05","50"], "11": ["11","66","16","61"], "22": ["22","77","27","72"], 
    "33": ["33","88","38","83"], "44": ["44","99","49","94"], 
    "01": ["01","10","06","60","51","15","56","65"], "02": ["02","20","07","70","25","52","57","75"],
    "03": ["03","30","08","80","35","53","58","85"], "04": ["04","40","09","90","45","54","59","95"], 
    "12": ["12","21","17","71","26","62","67","76"], "13": ["13","31","18","81","36","63","68","86"], 
    "14": ["14","41","19","91","46","64","69","96"], "23": ["23","32","28","82","73","37","78","87"],
    "24": ["24","42","29","92","74","47","79","97"], "34": ["34","43","39","93","84","48","89","98"]
}

ZODIAC_DICT = {
    "Tý": ["00","12","24","36","48","60","72","84","96"],
    "Sửu": ["01","13","25","37","49","61","73","85","97"],
    "Dần": ["02","14","26","38","50","62","74","86","98"],
    "Mão": ["03","15","27","39","51","63","75","87","99"],
    "Thìn": ["04","16","28","40","52","64","76","88"],
    "Tỵ": ["05","17","29","41","53","65","77","89"],
    "Ngọ": ["06","18","30","42","54","66","78","90"],
    "Mùi": ["07","19","31","43","55","67","79","91"],
    "Thân": ["08","20","32","44","56","68","80","92"],
    "Dậu": ["09","21","33","45","57","69","81","93"],
    "Tuất": ["10","22","34","46","58","70","82","94"],
    "Hợi": ["11","23","35","47","59","71","83","95"]
}

HIEU_MAP = {
    0: ["00","11","22","33","44","55","66","77","88","99"],
    1: ["09","10","21","32","43","54","65","76","87","98"],
    2: ["08","19","20","31","42","53","64","75","86","97"],
    3: ["07","18","29","30","41","52","63","74","85","96"],
    4: ["06","17","28","39","40","51","62","73","84","95"],
    5: ["05","16","27","38","49","50","61","72","83","94"],
    6: ["04","15","26","37","48","59","60","71","82","93"],
    7: ["03","14","25","36","47","58","69","70","81","92"],
    8: ["02","13","24","35","46","57","68","79","80","91"],
    9: ["01","12","23","34","45","56","67","78","89","90"]
}

# ============ HELPER FUNCTIONS ============
def bo(db: str) -> str:
    """Lấy bộ số từ 2 chữ số cuối"""
    db = db.zfill(2)
    if db in BO_DICT:
        return db
    for key, vals in BO_DICT.items():
        if db in vals:
            return key
    return "44"

def get_bo_dan(bo_key):
    return ",".join(BO_DICT.get(bo_key, []))

def kep(db: str) -> str:
    db = db.zfill(2)
    if db in {"07","70","14","41","29","92","36","63","58","85"}:
        return "K.ÂM"
    elif db in {"00","55","11","66","22","77","33","88","44","99"}:
        return "K.BẰNG"
    elif db in {"05","50","16","61","27","72","38","83","49","94"}:
        return "K.LỆCH"
    elif db in {"01","10","12","21","23","32","34","43","45","54","56","65","67","76","78","87","89","98","09","90"}:
        return "S.KÉP"
    return "KHÔNG"

def hieu(pair: str) -> int:
    p = pair.zfill(2)
    for delay, nums in HIEU_MAP.items():
        if p in nums:
            return delay
    return -1

def get_hieu_dan(h):
    return ",".join(HIEU_MAP.get(int(h), []))

def zodiac(pair: str) -> str:
    p = pair.zfill(2)
    for z, lst in ZODIAC_DICT.items():
        if p in lst:
            return z
    return "Không xác định"

def get_zodiac_dan(z):
    return ",".join(ZODIAC_DICT.get(z, []))

def get_tong_dan(tong):
    d = []
    for i in range(100):
        num = f"{i:02d}"
        if (int(num[0]) + int(num[1])) % 10 == int(tong):
            d.append(num)
    return ",".join(d)

def jn(rng, rnd):
    """Tính mức số - đếm số lần xuất hiện của mỗi cặp số"""
    counts = {f"{i:02d}": 0 for i in range(100)}
    for s in rng:
        for pair in counts:
            counts[pair] += s.count(pair)
    return ",".join(pair for pair, cnt in counts.items() if cnt == rnd)

def calculate_muc_so(dan_nuoi_list, compare_value=None):
    all_numbers = []
    for dan in dan_nuoi_list:
        numbers = dan.split()
        all_numbers.extend(numbers)
    
    all_possible_pairs = [f"{i:02d}" for i in range(100)]
    frequency = {pair: 0 for pair in all_possible_pairs}
    for num in all_numbers:
        frequency[num] = frequency.get(num, 0) + 1
    
    levels = {}
    for num, freq in frequency.items():
        if freq not in levels:
            levels[freq] = []
        levels[freq].append(num)
    
    result = {}
    for level in sorted(levels.keys(), reverse=True):
        pairs = sorted(levels[level], key=lambda x: int(x))
        result[level] = pairs
    return result

# ============ DATA FETCHING ============
@st.cache_data(ttl=3600)  # Cache 1 hour
def fetch_dien_toan_data():
    """Lấy dữ liệu Điện Toán 123"""
    try:
        url = f"https://ketqua04.net/so-ket-qua-dien-toan-123/{TOTAL_DAYS}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        divs = soup.find_all("div", class_="result_div", id="result_123")
        data = []
        for div in divs[:TOTAL_DAYS]:
            ds = div.find("span", id="result_date")
            date = ds.text.strip() if ds else ""
            tbl = div.find("table", id="result_tab_123")
            row = tbl.find("tbody").find("tr") if tbl else None
            cells = row.find_all("td") if row else []
            if len(cells) == 3 and all(c.text.strip().isdigit() for c in cells):
                nums = [c.text.strip() for c in cells]
                data.append({"date": date, "numbers": nums})
        return data
    except Exception as e:
        st.error(f"Lỗi lấy dữ liệu Điện Toán: {e}")
        return []

@st.cache_data(ttl=3600)
def fetch_than_tai_data():
    """Lấy dữ liệu Thần Tài"""
    try:
        url = f"https://ketqua04.net/so-ket-qua-than-tai/{TOTAL_DAYS}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        divs = soup.find_all("div", class_="result_div", id="result_tt4")
        data = []
        for div in divs[:TOTAL_DAYS]:
            ds = div.find("span", id="result_date")
            date = ds.text.strip() if ds else ""
            tbl = div.find("table", id="result_tab_tt4")
            cell = tbl.find("td", id="rs_0_0") if tbl else None
            num = cell.text.strip() if cell else ""
            if num.isdigit() and len(num) == 4:
                data.append({"date": date, "number": num})
        return data
    except Exception as e:
        st.error(f"Lỗi lấy dữ liệu Thần Tài: {e}")
        return []

@st.cache_data(ttl=3600)
def fetch_xsmb_data():
    """Lấy dữ liệu XSMB (Giải Đặc Biệt)"""
    try:
        url = "https://congcuxoso.com/MienBac/DacBiet/PhoiCauDacBiet/PhoiCauTuan5So.aspx"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        tbl = soup.find("table", id="MainContent_dgv")
        if not tbl:
            return []
        rows = tbl.find_all("tr")[1:]
        nums = []
        for row in reversed(rows):
            for cell in reversed(row.find_all("td")):
                t = cell.text.strip()
                if t and t not in ("-----", "\xa0"):
                    nums.append(t.zfill(5))
        
        dien_toan = fetch_dien_toan_data()
        data = []
        if dien_toan:
            N = min(len(nums), len(dien_toan), TOTAL_DAYS)
            for i in range(N):
                data.append({"date": dien_toan[i]["date"], "number": nums[i]})
        else:
            current_date = datetime.now()
            for i, num in enumerate(nums[:TOTAL_DAYS]):
                date_str = (current_date - timedelta(days=i)).strftime("Ngày %d/%m/%Y")
                data.append({"date": date_str, "number": num})
        return data
    except Exception as e:
        st.error(f"Lỗi lấy dữ liệu XSMB: {e}")
        return []

@st.cache_data(ttl=3600)
def fetch_giai_nhat_data():
    """Lấy dữ liệu Giải Nhất"""
    try:
        url = "https://congcuxoso.com/MienBac/GiaiNhat/PhoiCauGiaiNhat/PhoiCauTuan5So.aspx"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        tbl = soup.find("table", id="MainContent_dgv")
        if not tbl:
            return []
        rows = tbl.find_all("tr")[1:]
        nums = []
        for row in reversed(rows):
            for cell in reversed(row.find_all("td")):
                t = cell.text.strip()
                if t and t not in ("-----", "\xa0"):
                    nums.append(t.zfill(5))
        
        dien_toan = fetch_dien_toan_data()
        data = []
        if dien_toan:
            N = min(len(nums), len(dien_toan), TOTAL_DAYS)
            for i in range(N):
                data.append({"date": dien_toan[i]["date"], "number": nums[i]})
        else:
            current_date = datetime.now()
            for i, num in enumerate(nums[:TOTAL_DAYS]):
                date_str = (current_date - timedelta(days=i)).strftime("Ngày %d/%m/%Y")
                data.append({"date": date_str, "number": num})
        return data
    except Exception as e:
        st.error(f"Lỗi lấy dữ liệu Giải Nhất: {e}")
        return []

# ============ SIDEBAR ============
st.sidebar.title("🐔 SIÊU GÀ APP")
st.sidebar.markdown("---")

# Display mode selection
display_options = ["Hiện tại"] + [f"Lùi {i}" for i in range(1, 10)]
display_mode = st.sidebar.selectbox("📅 Chế độ hiển thị", display_options)

# Compare source selection
compare_source = st.sidebar.radio("📊 Nguồn so sánh", ["GĐB", "Giải Nhất"])

# Result type selection
result_type = st.sidebar.radio("🎯 Loại kết quả", ["Thần tài", "Điện toán"])

st.sidebar.markdown("---")
include_duplicates = st.sidebar.checkbox("Bao gồm số trùng", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("© TRUNGND2025")

# ============ MAIN CONTENT ============
st.title("🐔 SIÊU GÀ APP")
st.caption("Ứng dụng phân tích xổ số Miền Bắc")

# Load data
with st.spinner("Đang tải dữ liệu..."):
    dien_toan_data = fetch_dien_toan_data()
    than_tai_data = fetch_than_tai_data()
    xsmb_data = fetch_xsmb_data()
    giai_nhat_data = fetch_giai_nhat_data()

# Calculate offset
offset = 0 if display_mode == "Hiện tại" else int(display_mode.split()[-1])

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Kết Quả XS", 
    "🎲 Dàn Nuôi", 
    "📈 Mức Số",
    "📊 Thống Kê ĐB/G1",
    "ℹ️ Hướng Dẫn"
])

# ============ TAB 1: KẾT QUẢ XỔ SỐ ============
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎰 Điện Toán 123")
        if dien_toan_data:
            dt_slice = dien_toan_data[offset:offset + NUM_DAYS]
            df_dt = pd.DataFrame([
                {"Ngày": d["date"], "Số 1": d["numbers"][0], "Số 2": d["numbers"][1], "Số 3": d["numbers"][2]}
                for d in dt_slice
            ])
            st.dataframe(df_dt, use_container_width=True, height=400)
        
        st.subheader("🌟 Thần Tài")
        if than_tai_data:
            tt_slice = than_tai_data[offset:offset + NUM_DAYS]
            df_tt = pd.DataFrame([{"Ngày": d["date"], "Số": d["number"]} for d in tt_slice])
            st.dataframe(df_tt, use_container_width=True, height=400)
    
    with col2:
        st.subheader("🏆 Giải Đặc Biệt")
        if xsmb_data:
            xsmb_slice = xsmb_data[offset:offset + NUM_DAYS]
            df_xsmb = pd.DataFrame([{"Ngày": d["date"], "Số": d["number"]} for d in xsmb_slice])
            st.dataframe(df_xsmb, use_container_width=True, height=400)
        
        st.subheader("🥇 Giải Nhất")
        if giai_nhat_data:
            g1_slice = giai_nhat_data[offset:offset + NUM_DAYS]
            df_g1 = pd.DataFrame([{"Ngày": d["date"], "Số": d["number"]} for d in g1_slice])
            st.dataframe(df_g1, use_container_width=True, height=400)

# ============ TAB 2: DÀN NUÔI ============
with tab2:
    st.subheader("🎲 Dàn Nuôi ĐT+TT")
    
    if dien_toan_data and than_tai_data and xsmb_data:
        dt_slice = dien_toan_data[offset:offset + NUM_DAYS]
        tt_slice = than_tai_data[offset:offset + NUM_DAYS]
        xsmb_slice = xsmb_data[offset:offset + NUM_DAYS]
        g1_slice = giai_nhat_data[offset:offset + NUM_DAYS] if giai_nhat_data else []
        
        # Get results based on type
        if result_type == "Thần tài":
            results = [item["number"] for item in tt_slice]
        else:
            results = ["".join(item["numbers"]) for item in dt_slice]
        
        # Calculate Dàn Nuôi
        dan_nuoi_rows = []
        chua_ra_list = []
        
        for i in range(min(len(results), NUM_DAYS)):
            val = results[i]
            digits = list(val)
            
            # Nhị hợp
            combos = set()
            for a in digits:
                for b in digits:
                    pair = a + b
                    if include_duplicates or a != b:
                        combos.add(pair)
            
            # Comparison values
            if compare_source == "GĐB":
                C = [(xsmb_slice[i-k]["number"][-2:] if i >= k and i-k < len(xsmb_slice) else "") for k in range(1, 22)]
            else:
                C = [(g1_slice[i-k]["number"][-2:] if i >= k and i-k < len(g1_slice) else "") for k in range(1, 22)]
            
            K = [c if c in combos else "" for c in C]
            missing = [c for c in combos if c not in C]
            
            hit = "✅" if any(K) else "❌"
            
            if i <= 28 and all(x == "" for x in K):
                chua_ra_list.append(" ".join(sorted(combos)))
            
            dan_nuoi_rows.append({
                "Ngày": dt_slice[i]["date"] if i < len(dt_slice) else "",
                "KQ": val,
                "Dàn Nuôi": " ".join(sorted(combos)),
                "Hit": hit,
                "K1-K5": " | ".join(K[:5]),
            })
        
        df_dan = pd.DataFrame(dan_nuoi_rows)
        st.dataframe(df_dan, use_container_width=True, height=500)
        
        # Mức Số từ dàn chưa ra
        if chua_ra_list:
            st.subheader("📊 Mức Số từ Dàn Chưa Ra")
            muc_so = calculate_muc_so(chua_ra_list)
            for level, pairs in list(muc_so.items())[:10]:  # Top 10 levels
                if pairs:
                    st.markdown(f"**Mức {level}**: {len(pairs)} số ({', '.join(pairs[:20])}{'...' if len(pairs) > 20 else ''})")

# ============ TAB 3: MỨC SỐ ============
with tab3:
    st.subheader("📈 Lên Dàn Số Nuôi")
    
    # Helper function tính toán dàn lâu ra
    def calculate_lau_ra(results, xsmb_slice, g1_slice, compare_source, empty_threshold, dt_slice):
        n = len(results)
        lau_ra_list = []
        
        for i in range(min(NUM_DAYS, n)):
            start = i if i <= n - 7 else max(0, n - 7)
            window = results[start:start + 7]
            
            M_values = [jn(window, k) for k in range(1, 8)]
            pairs = []
            for m in M_values:
                if m:
                    pairs.extend(m.split(","))
            pairs_sorted = sorted(set(pairs), key=lambda x: int(x))
            dan_nuoi = " ".join(pairs_sorted)
            
            if compare_source == "GĐB":
                C = [(xsmb_slice[i-k]["number"][-2:] if i >= k and i-k < len(xsmb_slice) else "") for k in range(1, 29)]
            else:
                C = [(g1_slice[i-k]["number"][-2:] if i >= k and i-k < len(g1_slice) else "") for k in range(1, 29)]
            
            K = [c if c in pairs_sorted else "" for c in C]
            
            last_k_index = -1
            valid_k_range = min(i + 1, len(K))
            for j in range(valid_k_range - 1, -1, -1):
                if K[j] != "":
                    last_k_index = j
                    break
            empty_count = valid_k_range if last_k_index == -1 else max(0, (valid_k_range - 1 - last_k_index) - 1)
            
            if empty_count >= empty_threshold and i <= 28 and dan_nuoi:
                lau_ra_list.append((results[i], dan_nuoi))
        
        return lau_ra_list
    
    # Auto-reduce threshold function
    def get_lau_ra_with_auto_reduce(results, xsmb_slice, g1_slice, compare_source, initial_threshold, dt_slice):
        threshold = initial_threshold
        lau_ra = calculate_lau_ra(results, xsmb_slice, g1_slice, compare_source, threshold, dt_slice)
        actual_threshold = threshold
        
        # Tự động giảm threshold nếu không có dàn lâu ra
        while not lau_ra and threshold > 1:
            threshold -= 1
            lau_ra = calculate_lau_ra(results, xsmb_slice, g1_slice, compare_source, threshold, dt_slice)
            actual_threshold = threshold
        
        return lau_ra, actual_threshold
    
    # Controls row
    ctrl_col1, ctrl_col2 = st.columns(2)
    with ctrl_col1:
        empty_tt = st.slider("Ô rỗng TT ≥", 1, 10, 4, key="empty_tt")
    with ctrl_col2:
        empty_dt = st.slider("Ô rỗng ĐT ≥", 1, 10, 4, key="empty_dt")
    
    if dien_toan_data and than_tai_data and xsmb_data:
        dt_slice = dien_toan_data[offset:offset + NUM_DAYS]
        tt_slice = than_tai_data[offset:offset + NUM_DAYS]
        xsmb_slice = xsmb_data[offset:offset + NUM_DAYS]
        g1_slice = giai_nhat_data[offset:offset + NUM_DAYS] if giai_nhat_data else []
        
        # Tính dàn lâu ra cho cả 2 loại với auto-reduce
        results_tt = [item["number"] for item in tt_slice]
        results_dt = ["".join(item["numbers"]) for item in dt_slice]
        
        lau_ra_tt, actual_tt = get_lau_ra_with_auto_reduce(results_tt, xsmb_slice, g1_slice, compare_source, empty_tt, dt_slice)
        lau_ra_dt, actual_dt = get_lau_ra_with_auto_reduce(results_dt, xsmb_slice, g1_slice, compare_source, empty_dt, dt_slice)
        
        # ============ 2 CỘT: THẦN TÀI | ĐIỆN TOÁN ============
        col_tt, col_dt = st.columns(2)
        
        # Variables để lưu mức số cho backtest
        muc_tt_results = []
        muc_dt_results = []
        
        # ===== CỘT THẦN TÀI =====
        with col_tt:
            st.markdown("### 🌟 Thần Tài")
            if actual_tt != empty_tt:
                st.warning(f"⚠️ Auto-giảm xuống {actual_tt} ô rỗng")
            
            if lau_ra_tt:
                all_dan_tt = "\n".join([dan for _, dan in lau_ra_tt])
                st.text_area("Dàn Lâu Ra TT:", all_dan_tt, height=120, key="dan_tt")
                
                dan_list_tt = [dan for _, dan in lau_ra_tt]
                n_dan_tt = len(dan_list_tt)
                
                st.markdown("#### Chọn mức TT để lên dàn")
                for level in range(n_dan_tt + 1):
                    pairs = jn(dan_list_tt, level)
                    if pairs:
                        pairs_list = pairs.split(",")
                        muc_tt_results.append({
                            "level": level,
                            "count": len(pairs_list),
                            "pairs": pairs,
                            "pairs_set": set(pairs_list)
                        })
                
                # Checkbox cho mỗi mức với hiển thị đầy đủ số
                selected_tt = []
                for muc in muc_tt_results:
                    col_cb, col_num = st.columns([1, 3])
                    with col_cb:
                        checked = st.checkbox(
                            f"Mức {muc['level']}: {muc['count']} số", 
                            value=(muc['level'] <= 2),
                            key=f"cb_tt_{muc['level']}"
                        )
                    with col_num:
                        st.caption(muc['pairs'])
                    if checked:
                        selected_tt.extend(muc['pairs'].split(","))
                
                # Tổng hợp các mức đã chọn
                if selected_tt:
                    unique_tt = sorted(set(selected_tt), key=lambda x: int(x))
                    st.markdown(f"**Dàn TT đã chọn: {len(unique_tt)} số**")
                    st.code(",".join(unique_tt), language=None)
            else:
                selected_tt = []
                st.info("Không có dàn lâu ra")
        
        # ===== CỘT ĐIỆN TOÁN =====
        with col_dt:
            st.markdown("### 🎰 Điện Toán")
            if actual_dt != empty_dt:
                st.warning(f"⚠️ Auto-giảm xuống {actual_dt} ô rỗng")
            
            if lau_ra_dt:
                all_dan_dt = "\n".join([dan for _, dan in lau_ra_dt])
                st.text_area("Dàn Lâu Ra ĐT:", all_dan_dt, height=120, key="dan_dt")
                
                dan_list_dt = [dan for _, dan in lau_ra_dt]
                n_dan_dt = len(dan_list_dt)
                
                st.markdown("#### Chọn mức ĐT để lên dàn")
                for level in range(n_dan_dt + 1):
                    pairs = jn(dan_list_dt, level)
                    if pairs:
                        pairs_list = pairs.split(",")
                        muc_dt_results.append({
                            "level": level,
                            "count": len(pairs_list),
                            "pairs": pairs,
                            "pairs_set": set(pairs_list)
                        })
                
                # Checkbox cho mỗi mức với hiển thị đầy đủ số
                selected_dt = []
                for muc in muc_dt_results:
                    col_cb, col_num = st.columns([1, 3])
                    with col_cb:
                        checked = st.checkbox(
                            f"Mức {muc['level']}: {muc['count']} số", 
                            value=(muc['level'] <= 2),
                            key=f"cb_dt_{muc['level']}"
                        )
                    with col_num:
                        st.caption(muc['pairs'])
                    if checked:
                        selected_dt.extend(muc['pairs'].split(","))
                
                # Tổng hợp các mức đã chọn
                if selected_dt:
                    unique_dt = sorted(set(selected_dt), key=lambda x: int(x))
                    st.markdown(f"**Dàn ĐT đã chọn: {len(unique_dt)} số**")
                    st.code(",".join(unique_dt), language=None)
            else:
                selected_dt = []
                st.info("Không có dàn lâu ra")
        
        # ============ TỔNG HỢP TT + ĐT ============
        st.markdown("---")
        st.subheader("🎯 Tổng Hợp TT + ĐT")
        
        # Gộp các số đã chọn từ cả 2 nguồn
        all_selected = []
        if 'selected_tt' in dir() and selected_tt:
            all_selected.extend(selected_tt)
        if 'selected_dt' in dir() and selected_dt:
            all_selected.extend(selected_dt)
        
        if all_selected:
            from collections import Counter
            freq = Counter(all_selected)
            
            # Nhóm theo tần suất (mức)
            freq_groups = {}
            for num, count in freq.items():
                if count not in freq_groups:
                    freq_groups[count] = []
                freq_groups[count].append(num)
            
            # Tính Mức 0 - các số không xuất hiện trong dàn đã chọn
            all_nums = set(f"{i:02d}" for i in range(100))
            selected_set = set(all_selected)
            muc_0 = sorted(all_nums - selected_set, key=lambda x: int(x))
            
            # Hiển thị từng mức với code block để copy
            for level in sorted(freq_groups.keys(), reverse=True):
                nums = sorted(freq_groups[level], key=lambda x: int(x))
                st.markdown(f"**Mức {level}: {len(nums)} số**")
                st.code(",".join(nums), language=None)
            
            # Hiển thị Mức 0
            if muc_0:
                st.markdown(f"**Mức 0: {len(muc_0)} số** (không xuất hiện)")
                st.code(",".join(muc_0), language=None)
        else:
            st.info("Chưa chọn mức nào từ TT hoặc ĐT")
        
        # ============ BẢNG TEST NGƯỢC (BACKTEST) ============
        st.markdown("---")
        st.subheader("📊 Bảng Test Ngược 10 Ngày (Backtest)")
        st.caption(f"Mỗi ngày tính lại mức số với ô rỗng TT≥{empty_tt}, ĐT≥{empty_dt}")
        
        # Helper function tính mức số cho một offset cụ thể
        def calculate_muc_for_offset(back_offset, result_type_calc):
            # Lấy dữ liệu tại thời điểm lùi back_offset ngày
            local_dt_slice = dien_toan_data[back_offset:back_offset + NUM_DAYS]
            local_tt_slice = than_tai_data[back_offset:back_offset + NUM_DAYS]
            local_xsmb_slice = xsmb_data[back_offset:back_offset + NUM_DAYS]
            local_g1_slice = giai_nhat_data[back_offset:back_offset + NUM_DAYS] if giai_nhat_data else []
            
            if result_type_calc == "TT":
                local_results = [item["number"] for item in local_tt_slice]
                threshold = empty_tt
            else:
                local_results = ["".join(item["numbers"]) for item in local_dt_slice]
                threshold = empty_dt
            
            # Tính dàn lâu ra với auto-reduce
            local_lau_ra, _ = get_lau_ra_with_auto_reduce(
                local_results, local_xsmb_slice, local_g1_slice, 
                compare_source, threshold, local_dt_slice
            )
            
            if not local_lau_ra:
                return []
            
            # Tính mức số
            dan_list = [dan for _, dan in local_lau_ra]
            muc_results = []
            for level in range(len(dan_list) + 1):
                pairs = jn(dan_list, level)
                if pairs:
                    pairs_list = pairs.split(",")
                    muc_results.append({
                        "level": level,
                        "pairs_set": set(pairs_list)
                    })
            return muc_results
        
        # Tính backtest - bắt đầu từ offset hiện tại
        backtest_rows = []
        base_label = "" if offset == 0 else f"Lùi {offset}+"
        
        for i in range(1, 11):  # Test 10 ngày ngược từ vị trí hiện tại
            actual_offset = offset + i  # Offset thực tế = offset sidebar + i
            
            # Tính mức số tại thời điểm actual_offset
            muc_tt_at_i = calculate_muc_for_offset(actual_offset, "TT")
            muc_dt_at_i = calculate_muc_for_offset(actual_offset, "DT")
            
            # Lấy kết quả ngày trước đó (actual_offset - 1), tức là kết quả mà mức số dự đoán
            prev_offset = actual_offset - 1
            if compare_source == "GĐB":
                result_num = xsmb_data[prev_offset]["number"][-2:].zfill(2) if prev_offset < len(xsmb_data) else "-"
            else:
                result_num = giai_nhat_data[prev_offset]["number"][-2:].zfill(2) if prev_offset < len(giai_nhat_data) else "-"
            
            result_date = dien_toan_data[prev_offset]["date"] if prev_offset < len(dien_toan_data) else f"N-{prev_offset}"
            
            # Tìm mức nào chứa kết quả cho TT
            hit_muc_tt = "-"
            for muc in muc_tt_at_i:
                if result_num in muc["pairs_set"]:
                    hit_muc_tt = f"M{muc['level']}"
                    break
            
            # Tìm mức nào chứa kết quả cho DT
            hit_muc_dt = "-"
            for muc in muc_dt_at_i:
                if result_num in muc["pairs_set"]:
                    hit_muc_dt = f"M{muc['level']}"
                    break
            
            backtest_rows.append({
                "Lùi": f"{base_label}{i}" if base_label else f"Lùi {i}",
                "Ngày KQ": result_date,
                f"{compare_source}": result_num,
                "TT Mức": hit_muc_tt,
                "ĐT Mức": hit_muc_dt
            })
        
        df_backtest = pd.DataFrame(backtest_rows)
        st.dataframe(df_backtest, use_container_width=True, height=400)
        
        # Thống kê hit rate
        st.markdown("### 📈 Thống Kê Hit Rate")
        
        col_stat1, col_stat2 = st.columns(2)
        
        with col_stat1:
            st.markdown("**🌟 Thần Tài:**")
            tt_hits = [r["TT Mức"] for r in backtest_rows if r["TT Mức"] != "-"]
            tt_hit_rate = len(tt_hits) / len(backtest_rows) * 100 if backtest_rows else 0
            st.metric("Hit Rate", f"{tt_hit_rate:.0f}%", f"{len(tt_hits)}/10")
            
            from collections import Counter
            tt_counter = Counter(tt_hits)
            for muc, count in sorted(tt_counter.items()):
                st.caption(f"{muc}: {count} lần")
        
        with col_stat2:
            st.markdown("**🎰 Điện Toán:**")
            dt_hits = [r["ĐT Mức"] for r in backtest_rows if r["ĐT Mức"] != "-"]
            dt_hit_rate = len(dt_hits) / len(backtest_rows) * 100 if backtest_rows else 0
            st.metric("Hit Rate", f"{dt_hit_rate:.0f}%", f"{len(dt_hits)}/10")
            
            dt_counter = Counter(dt_hits)
            for muc, count in sorted(dt_counter.items()):
                st.caption(f"{muc}: {count} lần")

# ============ TAB 4: THỐNG KÊ ĐB/G1 ============
with tab4:
    st.subheader("📊 Thống Kê Giải Đặc Biệt / Giải Nhất")
    
    source_data = xsmb_data if compare_source == "GĐB" else giai_nhat_data
    
    if source_data:
        last2 = [item["number"][-2:].zfill(2) for item in source_data[:100]]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🎯 Bộ Số")
            bo_lau_ra = {}
            for b in set(bo(n) for n in last2):
                idx = next((i for i, n in enumerate(last2) if bo(n) == b), -1)
                bo_lau_ra[b] = idx
            
            bo_sorted = sorted(bo_lau_ra.items(), key=lambda x: x[1], reverse=True)
            for b, lag in bo_sorted[:5]:
                st.markdown(f"**Bộ {b}**: Lâu ra {lag} ngày")
                st.caption(f"Dàn: {get_bo_dan(b)}")
        
        with col2:
            st.markdown("### 🔢 Tổng")
            tong_lau_ra = {}
            for t in range(10):
                idx = next((i for i, n in enumerate(last2) if (int(n[0]) + int(n[1])) % 10 == t), -1)
                tong_lau_ra[t] = idx
            
            tong_sorted = sorted(tong_lau_ra.items(), key=lambda x: x[1], reverse=True)
            for t, lag in tong_sorted[:5]:
                st.markdown(f"**Tổng {t}**: Lâu ra {lag} ngày")
                st.caption(f"Dàn: {get_tong_dan(t)}")
        
        with col3:
            st.markdown("### 🐲 Con Giáp")
            zodiac_lau_ra = {}
            for z in set(zodiac(n) for n in last2):
                idx = next((i for i, n in enumerate(last2) if zodiac(n) == z), -1)
                zodiac_lau_ra[z] = idx
            
            zodiac_sorted = sorted(zodiac_lau_ra.items(), key=lambda x: x[1], reverse=True)
            for z, lag in zodiac_sorted[:5]:
                st.markdown(f"**{z}**: Lâu ra {lag} ngày")
                st.caption(f"Dàn: {get_zodiac_dan(z)}")
        
        st.markdown("---")
        
        col4, col5 = st.columns(2)
        
        with col4:
            st.markdown("### ➗ Hiệu")
            hieu_lau_ra = {}
            for h in range(10):
                idx = next((i for i, n in enumerate(last2) if hieu(n) == h), -1)
                hieu_lau_ra[h] = idx
            
            hieu_sorted = sorted(hieu_lau_ra.items(), key=lambda x: x[1], reverse=True)
            for h, lag in hieu_sorted[:5]:
                st.markdown(f"**Hiệu {h}**: Lâu ra {lag} ngày")
                st.caption(f"Dàn: {get_hieu_dan(h)}")
        
        with col5:
            st.markdown("### 👯 Kép")
            kep_lau_ra = {}
            for k in set(kep(n) for n in last2):
                idx = next((i for i, n in enumerate(last2) if kep(n) == k), -1)
                kep_lau_ra[k] = idx
            
            kep_sorted = sorted(kep_lau_ra.items(), key=lambda x: x[1], reverse=True)
            for k, lag in kep_sorted:
                if lag > 0:
                    st.markdown(f"**{k}**: Lâu ra {lag} ngày")

# ============ TAB 5: HƯỚNG DẪN ============
with tab5:
    st.subheader("ℹ️ Hướng Dẫn Sử Dụng")
    
    st.markdown("""
    ### 📱 Giới thiệu
    **SIÊU GÀ APP** là ứng dụng phân tích xổ số Miền Bắc, hỗ trợ:
    - Xem kết quả Điện Toán 123, Thần Tài, Giải ĐB, Giải Nhất
    - Tính toán Dàn Nuôi theo phương pháp Nhị Hợp
    - Thống kê Mức Số, Lâu Ra
    - Phân tích Bộ, Tổng, Hiệu, Kép, Con Giáp
    
    ### 🎮 Cách sử dụng
    1. **Chọn chế độ hiển thị**: Xem dữ liệu hiện tại hoặc lùi 1-9 ngày
    2. **Chọn nguồn so sánh**: GĐB hoặc Giải Nhất
    3. **Chọn loại kết quả**: Thần Tài hoặc Điện Toán
    4. **Xem các tab**: Kết Quả XS, Dàn Nuôi, Mức Số, Thống Kê
    
    ### ⚠️ Lưu ý
    - Đây là ứng dụng **THỐNG KÊ** tham khảo
    - **KHÔNG** khuyến khích cá cược
    - Dữ liệu được cache 1 giờ, refresh trang để cập nhật
    
    ### 👨‍💻 Tác giả
    © TRUNGND2025
    """)

# Footer
st.markdown("---")
st.caption("📊 Dữ liệu thống kê tham khảo - Không khuyến khích cá cược | © TRUNGND2025")
