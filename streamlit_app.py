import streamlit as st
import pandas as pd
import logic
import data_fetcher

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(
    page_title="SIÊU GÀ MOBILE",
    page_icon="🐔",
    layout="wide",
    initial_sidebar_state="collapsed" # Tự động thu gọn menu trên mobile
)

# --- CSS TÙY CHỈNH CHO MOBILE ---
# Ép padding của bảng nhỏ lại tối đa để vừa màn hình điện thoại
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] { height: 40px; padding: 5px 10px; font-size: 14px; }
    /* Thu nhỏ padding của ô trong bảng */
    div[data-testid="stDataFrame"] div[class^="stDataFrame"] td {
        padding: 2px 5px !important; 
        font-size: 13px;
    }
    div[data-testid="stDataFrame"] div[class^="stDataFrame"] th {
        padding: 2px 5px !important;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# --- HÀM TIỆN ÍCH: RÚT GỌN NGÀY ---
def shorten_date(date_str):
    """Chuyển 'Thứ Tư ngày 19-11-2025' thành '19/11'"""
    try:
        # Lấy phần ngày tháng năm (ví dụ: 19-11-2025)
        parts = date_str.split(" ")
        raw_date = parts[-1] # Lấy phần tử cuối
        day_mon = raw_date[:5] # Lấy 5 ký tự đầu: 19-11
        return day_mon
    except:
        return date_str

# --- 1. QUẢN LÝ DỮ LIỆU (CACHE) ---
@st.cache_data(ttl=3600)
def load_all_data(num_days):
    dt = data_fetcher.fetch_dien_toan(num_days)
    tt = data_fetcher.fetch_than_tai(num_days)
    xsmb = data_fetcher.fetch_phoi_cau_xsmb(num_days, dt)
    g1 = data_fetcher.fetch_giai_nhat(num_days, dt)
    return dt, tt, xsmb, g1

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("🐔 SIÊU GÀ TOOL")
    days_fetch = st.number_input("Tải dữ liệu (ngày)", 50, 365, 100, step=50)
    days_show = st.slider("Hiển thị (ngày)", 5, 50, 20) # Mặc định ít ngày hơn cho mobile
    if st.button("🔄 Cập nhật"):
        st.cache_data.clear()
        st.rerun()

# --- LOAD DATA ---
try:
    with st.spinner("Đang tải..."):
        full_dt, full_tt, full_xsmb, full_g1 = load_all_data(days_fetch)
except Exception as e:
    st.error(f"Lỗi: {e}")
    st.stop()

# Cắt và RÚT GỌN NGÀY ngay từ đầu
dt_show = full_dt[:days_show]
tt_show = full_tt[:days_show]
xsmb_show = full_xsmb[:days_show]
g1_show = full_g1[:days_show]

# Hàm xử lý display data chung
def prepare_display_data(data):
    new_data = []
    for item in data:
        new_item = item.copy()
        new_item['date'] = shorten_date(item['date'])
        new_data.append(new_item)
    return new_data

dt_disp = prepare_display_data(dt_show)
tt_disp = prepare_display_data(tt_show)
xsmb_disp = prepare_display_data(xsmb_show)
g1_disp = prepare_display_data(g1_show)

# --- 3. MAIN TABS ---
# Đặt tên Tab ngắn gọn cho mobile
tabs = st.tabs(["KQ", "Nuôi", "Bệt", "Last2", "Dò"])

# === TAB 1: KẾT QUẢ ===
with tabs[0]:
    # Điện toán
    st.caption("Điện Toán 123")
    if dt_disp:
        df_dt = pd.DataFrame(dt_disp)
        df_dt['Số'] = df_dt['numbers'].apply(lambda x: "-".join(x))
        # Cấu hình bảng gọn
        st.dataframe(
            df_dt[['date', 'Số']], 
            hide_index=True, 
            use_container_width=True,
            column_config={
                "date": st.column_config.TextColumn("Ngày", width="small"),
                "Số": st.column_config.TextColumn("Kết Quả", width="medium")
            }
        )
    
    # Các đài khác gộp chung để đỡ scroll
    st.caption("Thần Tài | GĐB | G1")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("**Thần Tài**")
        if tt_disp: st.dataframe(pd.DataFrame(tt_disp), hide_index=True, use_container_width=True, column_config={"date":None, "number":"Số"})
    with c2:
        st.markdown("**GĐB**")
        if xsmb_disp: st.dataframe(pd.DataFrame(xsmb_disp), hide_index=True, use_container_width=True, column_config={"date":None, "number":"Số"})
    with c3:
        st.markdown("**Giải 1**")
        if g1_disp: st.dataframe(pd.DataFrame(g1_disp), hide_index=True, use_container_width=True, column_config={"date":None, "number":"Số"})

# === TAB 2: DÀN NUÔI (QUAN TRỌNG NHẤT) ===
with tabs[1]:
    st.caption("Phân Tích Dàn Nuôi")
    
    # Gom controls cho gọn
    c_src, c_type, c_dup = st.columns([1,1,1])
    source_comp = c_src.radio("So:", ["GĐB", "G1"], horizontal=True, label_visibility="collapsed")
    res_type = c_type.selectbox("Nguồn:", ["Thần tài", "Điện toán"], label_visibility="collapsed")
    include_dup = c_dup.checkbox("Kép", value=True)
    
    cham_filter = st.selectbox("Lọc chạm:", [""] + [str(i) for i in range(10)])

    if st.button("🚀 Chạy"):
        # Chọn nguồn dữ liệu (lấy từ bản gốc chưa rút gọn ngày để tính toán chính xác nếu cần)
        source_list = [x["number"] for x in tt_show] if res_type == "Thần tài" else ["".join(x["numbers"]) for x in dt_show]
        ref_data = full_xsmb if source_comp == "GĐB" else full_g1
        latest_ref_val = ref_data[0]["number"][-2:] if ref_data else ""
        
        results = []
        missed_patterns = []
        raw_missed_data = []

        for i in range(len(source_list)):
            val = source_list[i]
            digits = list(val)
            combos = {a+b for a in digits for b in digits}
            if not include_dup: combos = {c for c in combos if c[0] != c[1]}
            if cham_filter: combos = {c for c in combos if cham_filter in c}
            
            if not combos: continue

            check_range = 21
            k_cols = {}
            hits = 0
            
            for k in range(1, check_range + 1):
                check_idx = i - k
                val_ref = ""
                if check_idx >= 0: val_ref = ref_data[check_idx]["number"][-2:]
                
                status = val_ref if val_ref in combos else ""
                k_cols[f"K{k}"] = status
                if status: hits += 1
            
            # Dùng ngày đã rút gọn để hiển thị
            date_short = shorten_date(dt_show[i]['date'])
            
            row = {
                "Ngày": date_short,
                "KQ": val,
                "Dàn": " ".join(sorted(combos)),
                "TT": "NO" if hits > 0 else "MISS" # Viết tắt cho gọn cột
            }
            row.update(k_cols)
            results.append(row)
            
            if hits == 0 and i <= 30: 
                missed_str = " ".join(sorted(combos))
                missed_patterns.append(f"{date_short} ({val}): {missed_str}")
                raw_missed_data.append(missed_str)

        df_res = pd.DataFrame(results)
        
        def color_status(val):
            return f'background-color: {"#ffcccc" if val == "MISS" else "#ccffcc"}'

        if not df_res.empty:
            # CẤU HÌNH CỘT SIÊU GỌN CHO MOBILE
            col_config = {
                "Ngày": st.column_config.TextColumn("Ngày", width="small"),
                "KQ": st.column_config.TextColumn("KQ", width="small"), 
                "Dàn": st.column_config.TextColumn("Dàn", width="medium"),
                "TT": st.column_config.TextColumn("TT", width="small"),
            }
            
            # Cấu hình cột K: Đổi tên "K1" -> "1", ép width="small"
            k_cols_list = [c for c in df_res.columns if c.startswith("K")]
            for k_col in k_cols_list:
                col_config[k_col] = st.column_config.TextColumn(
                    k_col.replace("K", ""), 
                    width="small" # Ép nhỏ nhất có thể
                )

            st.dataframe(
                df_res.style.applymap(color_status, subset=['TT']),
                column_config=col_config,
                use_container_width=False, # Tắt giãn dòng để cột co lại
                hide_index=True,
                height=600
            )
        
        if missed_patterns:
            st.error(f"Dàn MISS (30 ngày):")
            # Tính mức số
            if raw_missed_data:
                from collections import Counter
                all_nums = " ".join(raw_missed_data).split()
                counts = Counter(all_nums)
                levels = {}
                for num, freq in counts.items(): levels.setdefault(freq, []).append(num)
                
                for lvl in sorted(levels.keys(), reverse=True):
                    nums = sorted(levels[lvl])
                    disp = [f"**{n}**" if n==latest_ref_val else n for n in nums]
                    st.markdown(f"**Mức {lvl}:** {', '.join(disp)}")

# === TAB 3: BỆT ===
with tabs[2]:
    st.caption("Thống Kê Bệt")
    b_src = st.selectbox("Nguồn:", ["GĐB", "G1", "Thần Tài"], label_visibility="collapsed")
    b_types = st.multiselect("Kiểu:", ["Bệt Phải", "Thẳng", "Bệt trái"], default=["Bệt Phải"])
    
    if b_src == "GĐB": s_dat = xsmb_show
    elif b_src == "G1": s_dat = g1_show
    else: s_dat = tt_show
    
    gdb_tails = [x['number'][-2:] for x in full_xsmb]
    
    b_rows = []
    for i in range(len(s_dat)-1):
        curr, nxt = s_dat[i], s_dat[i+1]
        found = set()
        for t in b_types:
            found.update(logic.tim_chu_so_bet(list(curr['number']), list(nxt['number']), t))
        
        if found:
            dancham = logic.lay_dan_cham(list(found))
            t1, t2 = gdb_tails[i], gdb_tails[i+1]
            nhihop = logic.lay_nhi_hop(list(found), list(t1)+list(t2))
            final = sorted(set(dancham + nhihop))
            res_mai = gdb_tails[i-1] if i-1 >= 0 else "?"
            
            b_rows.append({
                "Ngày": shorten_date(curr['date']),
                "Bệt": ",".join(sorted(found)),
                "Mai": f"{res_mai} ({'OK' if res_mai in final else '-'})"
            })
            
    st.dataframe(pd.DataFrame(b_rows), hide_index=True, use_container_width=True)

# === TAB 4: LAST2 ===
with tabs[3]:
    st.caption("Thống Kê 2 Số")
    l2_src = st.radio("Nguồn:", ["GĐB", "G1"], horizontal=True)
    dat_l2 = full_xsmb if l2_src == "GĐB" else full_g1
    
    l2_rows = []
    for x in dat_l2[:days_show]:
        n = x['number'][-2:]
        l2_rows.append({
            "Ngày": shorten_date(x['date']),
            "Số": n,
            "Bộ": logic.bo(n),
            "T": (int(n[0])+int(n[1]))%10,
        })
    st.dataframe(pd.DataFrame(l2_rows), hide_index=True, use_container_width=True)

# === TAB 5: DÒ CẦU ===
with tabs[4]:
    tgt = st.text_input("Tìm số (VD: 68):", max_chars=2)
    if tgt and len(tgt)==2:
        f = []
        for x in full_xsmb[:days_fetch]:
            if tgt in x['number']: f.append({"Ngày": shorten_date(x['date']), "Nguồn": "GĐB", "Số": x['number']})
        for x in full_g1[:days_fetch]:
            if tgt in x['number']: f.append({"Ngày": shorten_date(x['date']), "Nguồn": "G1", "Số": x['number']})
        if f: st.dataframe(pd.DataFrame(f), hide_index=True, use_container_width=True)
        else: st.caption("Không thấy")
