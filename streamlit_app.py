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

st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] { background-color: #f8f9fa; padding: 10px; border-radius: 5px; }
    .stTabs [aria-selected="true"] { background-color: #e8f0fe; border-bottom: 2px solid #4285f4; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- QUẢN LÝ DỮ LIỆU ---
@st.cache_data(ttl=1800)
def get_master_data(num_days):
    # 1. Tải song song các nguồn
    with concurrent.futures.ThreadPoolExecutor() as executor:
        f_dt = executor.submit(data_fetcher.fetch_dien_toan, num_days)
        f_tt = executor.submit(data_fetcher.fetch_than_tai, num_days)
        f_xsmb = executor.submit(data_fetcher.fetch_xsmb_group, num_days)
        
        dt_data = f_dt.result()
        tt_data = f_tt.result()
        xsmb_raw, g1_raw = f_xsmb.result()

    # 2. Chuẩn hóa thành DataFrame
    df_dt = pd.DataFrame(dt_data)
    df_tt = pd.DataFrame(tt_data)
    
    # 3. Xử lý ghép ngày cho XSMB (quan trọng để không lệch)
    # Sử dụng ngày của Điện toán làm chuẩn (vì XSMB trả về list không có ngày)
    xsmb_list = []
    limit = min(len(df_dt), len(xsmb_raw), len(g1_raw))
    
    for i in range(limit):
        xsmb_list.append({
            "date": df_dt.iloc[i]["date"], # Lấy ngày từ điện toán
            "xsmb_full": xsmb_raw[i],
            "xsmb_2so": xsmb_raw[i][-2:],
            "g1_full": g1_raw[i],
            "g1_2so": g1_raw[i][-2:]
        })
    df_xsmb = pd.DataFrame(xsmb_list)

    # 4. Merge tất cả thành 1 bảng Master
    if not df_dt.empty and not df_xsmb.empty:
        df_master = pd.merge(df_dt, df_tt, on="date", how="left")
        df_master = pd.merge(df_master, df_xsmb, on="date", how="left")
        return df_master
    return pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🐔 SIÊU GÀ TOOL")
    st.caption("Ver: 2.0 Fix")
    days_fetch = st.number_input("Số ngày tải:", 30, 365, 60)
    days_show = st.slider("Hiển thị:", 10, 100, 20)
    if st.button("🔄 Làm mới", type="primary"):
        st.cache_data.clear()
        st.rerun()

# --- MAIN ---
with st.spinner("🚀 Đang tải dữ liệu đa luồng..."):
    try:
        df_full = get_master_data(days_fetch)
        if df_full.empty:
            st.error("Không có dữ liệu. Vui lòng thử lại.")
            st.stop()
    except Exception as e:
        st.error(f"Lỗi: {e}")
        st.stop()

df_show = df_full.head(days_show).copy()

# --- TABS ---
tabs = st.tabs(["📊 KẾT QUẢ", "🎯 DÀN NUÔI", "🎲 BỆT CẦU", "📈 THỐNG KÊ L2", "🔍 TRA CỨU"])

# === TAB 1: KẾT QUẢ ===
with tabs[0]:
    st.markdown("#### Bảng Tổng Hợp")
    df_disp = df_show.copy()
    df_disp['Điện Toán'] = df_disp['dt_numbers'].apply(lambda x: " - ".join(x) if isinstance(x, list) else "")
    
    st.dataframe(
        df_disp[['date', 'Điện Toán', 'tt_number', 'xsmb_full', 'g1_full']],
        column_config={
            "date": "Ngày",
            "tt_number": "Thần Tài",
            "xsmb_full": "XSMB (ĐB)",
            "g1_full": "Giải Nhất"
        },
        hide_index=True, use_container_width=True
    )

# === TAB 2: DÀN NUÔI ===
with tabs[1]:
    c1, c2, c3 = st.columns([1,1,2])
    with c1: src_mode = st.selectbox("Nguồn:", ["Thần Tài", "Điện Toán"])
    with c2: comp_mode = st.selectbox("So với:", ["XSMB (ĐB)", "Giải Nhất"])
    with c3: check_range = st.slider("Khung nuôi:", 1, 30, 21)
    
    if st.button("🚀 Phân Tích"):
        res_list = []
        missed_list = []
        col_comp = "xsmb_2so" if comp_mode == "XSMB (ĐB)" else "g1_2so"
        
        for i in range(len(df_show)):
            row = df_full.iloc[i]
            # Lấy nguồn
            src_str = ""
            if src_mode == "Thần Tài" and row['tt_number']: src_str = row['tt_number']
            elif src_mode == "Điện Toán" and isinstance(row['dt_numbers'], list): src_str = "".join(row['dt_numbers'])
            
            if not src_str: continue
            
            # Tạo dàn
            digits = set(src_str)
            combos = {a+b for a in digits for b in digits}
            
            # Check win
            hits = 0
            k_cols = {}
            for k in range(1, check_range + 1):
                idx = i - k
                val_ref = df_full.iloc[idx][col_comp] if idx >= 0 else ""
                status = val_ref if val_ref in combos else ""
                k_cols[f"{k}"] = status
                if status: hits += 1
            
            r = {"Ngày": row['date'], "Nguồn": src_str, "Dàn": " ".join(sorted(combos)), "KQ": "✅" if hits else "⏳"}
            r.update(k_cols)
            res_list.append(r)
            
            if hits == 0 and i <= 30: missed_list.extend(list(combos))

        if res_list:
            df_res = pd.DataFrame(res_list)
            def style_row(v): return 'background-color: #d1e7dd' if v == "✅" else 'background-color: #f8d7da'
            st.dataframe(df_res.style.applymap(style_row, subset=['KQ']), hide_index=True, use_container_width=True)
            
            if missed_list:
                st.divider()
                st.write("🔥 **Mức Số (Từ dàn chưa nổ 30 ngày qua)**")
                from collections import Counter
                counts = Counter(missed_list)
                sorted_c = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                
                txt = ""
                for num, freq in sorted_c:
                    if freq >= 2: txt += f"**{num}**({freq})  "
                    else: txt += f"{num} "
                st.markdown(txt)

# === TAB 3: BỆT CẦU ===
with tabs[2]:
    st.write("Soi cầu bệt từ GĐB/G1/Thần tài sang XSMB ngày mai")
    # Logic tương tự code cũ nhưng dùng DataFrame df_full đã đồng bộ ngày
    # ... (Bạn có thể thêm logic bệt vào đây nếu cần, cấu trúc đã sẵn sàng)
    st.info("Đang cập nhật module này với dữ liệu mới...")

# === TAB 4: THỐNG KÊ ===
with tabs[3]:
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        st.write("Thống kê Bộ/Tổng")
        df_stat = pd.DataFrame({
            "Ngày": df_show['date'],
            "ĐB": df_show['xsmb_2so'],
            "Bộ": df_show['xsmb_2so'].apply(logic.bo),
            "Tổng": df_show['xsmb_2so'].apply(lambda x: str((int(x[0])+int(x[1]))%10) if x and x.isdigit() else "")
        })
        st.dataframe(df_stat, hide_index=True, use_container_width=True)
    
    with col_l2:
        st.write("🔴 **Top Bộ Gan**")
        all_tails = df_full['xsmb_2so'].dropna().tolist()
        last_seen = {}
        for idx, val in enumerate(all_tails):
            if not val.isdigit(): continue
            b = logic.bo(val)
            if b not in last_seen: last_seen[b] = idx
        
        df_gan = pd.DataFrame(list(last_seen.items()), columns=['Bộ', 'Số ngày gan'])
        st.dataframe(df_gan.sort_values('Số ngày gan', ascending=False).head(10), hide_index=True)

# === TAB 5: TRA CỨU ===
with tabs[4]:
    f_num = st.text_input("Nhập số cần tìm (VD: 68)", max_chars=2)
    if f_num:
        mask = df_full.apply(lambda r: f_num in str(r['xsmb_full']) or f_num in str(r['g1_full']), axis=1)
        st.dataframe(df_full[mask][['date', 'xsmb_full', 'g1_full']], hide_index=True, use_container_width=True)
