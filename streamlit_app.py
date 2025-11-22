import streamlit as st
import pandas as pd
import logic
import data_fetcher
import concurrent.futures

# --- CẤU HÌNH ---
st.set_page_config(
    page_title="SIÊU GÀ APP - PRO",
    page_icon="🐔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS FIX LỖI FONT & GIAO DIỆN ---
st.markdown("""
<style>
    /* Fix lỗi font menu bị chìm trong dark mode */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #e0e0e0;
        border-radius: 5px 5px 0 0;
        padding: 10px;
        color: #000000 !important; /* Ép màu chữ đen */
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ff4b4b !important;
        color: #ffffff !important;
        border-top: 2px solid #ff4b4b;
    }
    /* Căn giữa ô bảng */
    .stDataFrame td { vertical-align: middle !important; }
</style>
""", unsafe_allow_html=True)

# --- QUẢN LÝ DỮ LIỆU ---
@st.cache_data(ttl=1800)
def get_master_data(num_days):
    # Tải song song tất cả các nguồn
    with concurrent.futures.ThreadPoolExecutor() as executor:
        f_dt = executor.submit(data_fetcher.fetch_dien_toan, num_days)
        f_tt = executor.submit(data_fetcher.fetch_than_tai, num_days)
        f_mb = executor.submit(data_fetcher.fetch_xsmb_group, num_days)
        
        dt = f_dt.result()
        tt = f_tt.result()
        mb_db, mb_g1 = f_mb.result()

    # Xử lý khớp ngày (Quan trọng để không bị lệch)
    df_dt = pd.DataFrame(dt)
    df_tt = pd.DataFrame(tt)
    
    xsmb_rows = []
    limit = min(len(dt), len(mb_db), len(mb_g1))
    for i in range(limit):
        xsmb_rows.append({
            "date": dt[i]["date"], # Dùng ngày của Điện Toán làm chuẩn
            "xsmb_full": mb_db[i],
            "xsmb_2so": mb_db[i][-2:],
            "g1_full": mb_g1[i],
            "g1_2so": mb_g1[i][-2:]
        })
    df_xsmb = pd.DataFrame(xsmb_rows)

    # Gộp thành bảng tổng (Master Table)
    if not df_dt.empty and not df_xsmb.empty:
        df = pd.merge(df_dt, df_tt, on="date", how="left")
        df = pd.merge(df, df_xsmb, on="date", how="left")
        return df
    return pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🐔 SIÊU GÀ TOOL")
    st.caption("Version: Matrix View")
    days_fetch = st.number_input("Số ngày tải:", 30, 365, 60, step=10)
    days_show = st.slider("Hiển thị:", 10, 100, 20)
    if st.button("🔄 Tải lại dữ liệu", type="primary"):
        st.cache_data.clear()
        st.rerun()

# --- LOAD DATA ---
try:
    with st.spinner("🚀 Đang tải dữ liệu đa luồng..."):
        df_full = get_master_data(days_fetch)
        if df_full.empty:
            st.error("Không có dữ liệu. Kiểm tra kết nối mạng.")
            st.stop()
except Exception as e:
    st.error(f"Lỗi: {e}")
    st.stop()

df_show = df_full.head(days_show).copy()

# --- TABS ---
tabs = st.tabs(["📊 KẾT QUẢ", "🎯 DÀN NUÔI (MATRIX)", "🎲 BỆT CẦU", "🔍 TRA CỨU"])

# === TAB 1: KẾT QUẢ ===
with tabs[0]:
    df_disp = df_show.copy()
    df_disp['Điện Toán'] = df_disp['dt_numbers'].apply(lambda x: " - ".join(x) if isinstance(x, list) else "")
    
    st.dataframe(
        df_disp[['date', 'Điện Toán', 'tt_number', 'xsmb_full', 'g1_full']],
        column_config={
            "date": st.column_config.TextColumn("Ngày", width="small"),
            "Điện Toán": "Điện Toán 123",
            "tt_number": "Thần Tài",
            "xsmb_full": "Đặc Biệt",
            "g1_full": "Giải Nhất"
        },
        hide_index=True, use_container_width=True
    )

# === TAB 2: DÀN NUÔI (MATRIX VIEW) ===
with tabs[1]:
    c1, c2, c3 = st.columns([1, 1, 2])
    src_mode = c1.selectbox("Nguồn:", ["Thần Tài", "Điện Toán"])
    comp_mode = c2.selectbox("So với:", ["XSMB (ĐB)", "Giải Nhất"])
    check_range = c3.slider("Khung nuôi (ngày):", 1, 20, 7)
    
    if st.button("🚀 Phân Tích Bảng Chéo", type="primary"):
        res_list = []
        col_comp = "xsmb_2so" if comp_mode == "XSMB (ĐB)" else "g1_2so"
        
        for i in range(len(df_show)):
            row = df_full.iloc[i]
            # Lấy nguồn số
            src_str = ""
            if src_mode == "Thần Tài": src_str = str(row.get('tt_number', ''))
            elif src_mode == "Điện Toán": src_str = "".join(row.get('dt_numbers', []))
            
            if not src_str or src_str == "nan": continue
            
            # Tạo dàn
            digits = set(src_str)
            combos = {a+b for a in digits for b in digits}
            
            # Check các ngày tương lai (Quá khứ so với index hiện tại)
            k_cols = {}
            hits = 0
            first_hit = ""
            
            for k in range(1, check_range + 1):
                idx = i - k
                val_res = ""
                cell_val = "" # Giá trị hiển thị trong ô
                
                if idx >= 0:
                    val_res = df_full.iloc[idx][col_comp]
                    if val_res in combos:
                        hits += 1
                        cell_val = f"✅ {val_res}"
                        if not first_hit: first_hit = f"N{k}"
                
                k_cols[f"{k}"] = cell_val # Cột 1, 2, 3...
            
            r = {
                "Ngày": row['date'],
                "Nguồn": src_str,
                "SL": len(combos),
                "KQ": f"Ăn {first_hit}" if hits else "⏳"
            }
            r.update(k_cols)
            res_list.append(r)
            
        if res_list:
            df_res = pd.DataFrame(res_list)
            
            # Config cột động
            col_cfg = {
                "Ngày": st.column_config.TextColumn("Ngày", width="small"),
                "Nguồn": st.column_config.TextColumn("Nguồn", width="small"),
                "SL": st.column_config.TextColumn("Dàn", width="small"),
                "KQ": st.column_config.TextColumn("Trạng thái", width="small"),
            }
            # Các cột ngày K thu nhỏ lại
            cols_k = [str(k) for k in range(1, check_range + 1)]
            for k in cols_k:
                col_cfg[k] = st.column_config.TextColumn(f"N{k}", width="small")
            
            # Style màu sắc
            def highlight_cells(val):
                if "✅" in str(val):
                    return 'background-color: #d4edda; color: green; font-weight: bold; text-align: center'
                return ''
            
            def highlight_status(val):
                return 'background-color: #c3e6cb; color: darkgreen' if "Ăn" in str(val) else 'background-color: #f8d7da; color: maroon'

            st.dataframe(
                df_res.style.applymap(highlight_cells, subset=cols_k)
                            .applymap(highlight_status, subset=['KQ']),
                column_config=col_cfg,
                hide_index=True, use_container_width=True
            )
            st.caption(f"*Chú thích: N1, N2... là ngày thứ 1, thứ 2 sau khi có cầu. Ô tích xanh là trúng.*")

# === TAB 3: BỆT CẦU ===
with tabs[2]:
    st.subheader("Soi Cầu Bệt (GĐB/G1)")
    # Logic soi cầu bệt đơn giản
    bet_data = []
    for i in range(len(df_show) - 1):
        curr = df_show.iloc[i]['xsmb_full']
        prev = df_show.iloc[i+1]['xsmb_full']
        if not curr or not prev: continue
        
        # Tìm bệt thẳng
        d1, d2 = list(curr), list(prev)
        bet_nums = logic.tim_chu_so_bet(d1, d2, "Thẳng")
        
        if bet_nums:
             bet_data.append({
                 "Ngày": df_show.iloc[i]['date'],
                 "Hôm nay": curr,
                 "Hôm qua": prev,
                 "Số Bệt": ",".join(bet_nums)
             })
    
    if bet_data:
        st.dataframe(pd.DataFrame(bet_data), use_container_width=True)
    else:
        st.info("Không tìm thấy cầu bệt trong phạm vi hiển thị.")

# === TAB 4: TRA CỨU ===
with tabs[3]:
    f_num = st.text_input("Nhập số cần tìm (VD: 88):", max_chars=2)
    if f_num:
        mask = df_full.apply(lambda r: f_num in str(r['xsmb_full']) or f_num in str(r['g1_full']), axis=1)
        found = df_full[mask][['date', 'xsmb_full', 'g1_full']]
        if not found.empty:
            st.success(f"Tìm thấy {len(found)} kết quả.")
            st.dataframe(found, use_container_width=True)
        else:
            st.warning("Không tìm thấy.")
