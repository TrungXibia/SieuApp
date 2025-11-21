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
    .stTabs [data-baseweb="tab"] { background-color: #f8f9fa; border-radius: 4px; padding: 10px; }
    .stTabs [aria-selected="true"] { background-color: #e8f0fe; border-bottom: 2px solid #4285f4; font-weight: bold; }
    div[data-testid="stMetric"] { background-color: #f0f2f6; padding: 10px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# --- QUẢN LÝ DỮ LIỆU ---
@st.cache_data(ttl=1800)
def get_master_data(num_days):
    # Tải song song 2 luồng chính: (Điện toán + Thần tài) và (Nhóm XSMB)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        f_dt = executor.submit(data_fetcher.fetch_dien_toan, num_days)
        f_tt = executor.submit(data_fetcher.fetch_than_tai, num_days)
        
        dt_data = f_dt.result()
        tt_data = f_tt.result()
        
        # XSMB và G1 cần date reference từ Điện toán để khớp ngày
        xsmb_g1_data = data_fetcher.fetch_xsmb_and_g1(num_days, dt_data)
        
    # Chuyển đổi sang DataFrame
    df_dt = pd.DataFrame(dt_data)
    df_tt = pd.DataFrame(tt_data)
    df_xsmb = pd.DataFrame(xsmb_g1_data)
    
    # Merge dữ liệu lại thành 1 bảng Master theo 'date'
    if not df_dt.empty and not df_xsmb.empty:
        # Merge Left để ưu tiên ngày của Điện toán
        df_master = pd.merge(df_dt, df_tt, on="date", how="left")
        df_master = pd.merge(df_master, df_xsmb, on="date", how="left")
        return df_master
    return pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🐔 SIÊU GÀ TOOL")
    st.caption("Ver: 2.0 (Turbo)")
    st.markdown("---")
    days_fetch = st.number_input("Số ngày tải dữ liệu", 30, 365, 60, step=10)
    days_show = st.slider("Số ngày hiển thị", 10, 100, 20)
    
    if st.button("🔄 Làm mới dữ liệu", type="primary"):
        st.cache_data.clear()
        st.rerun()

# --- LOAD DATA ---
with st.spinner("🚀 Đang xử lý dữ liệu đa luồng..."):
    try:
        df_full = get_master_data(days_fetch)
        if df_full.empty:
            st.error("Không tải được dữ liệu. Vui lòng thử lại sau.")
            st.stop()
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
        st.stop()

# Cắt dữ liệu hiển thị
df_show = df_full.head(days_show).copy()

# --- TABS ---
tabs = st.tabs(["📊 KẾT QUẢ", "🎯 DÀN NUÔI", "🎲 BỆT CẦU", "📈 THỐNG KÊ L2", "🔍 TRA CỨU"])

# === TAB 1: KẾT QUẢ ===
with tabs[0]:
    st.markdown("#### Bảng Kết Quả Tổng Hợp")
    # Format dữ liệu để hiển thị đẹp hơn
    df_display = df_show.copy()
    df_display['Điện Toán'] = df_display['dt_numbers'].apply(lambda x: " - ".join(x) if isinstance(x, list) else "")
    
    col_cfg = {
        "date": st.column_config.TextColumn("Ngày", width="small"),
        "Điện Toán": st.column_config.TextColumn("Điện Toán 123", width="medium"),
        "tt_number": st.column_config.TextColumn("Thần Tài", width="small"),
        "xsmb_full": st.column_config.TextColumn("XSMB (ĐB)", width="small"),
        "g1_full": st.column_config.TextColumn("Giải Nhất", width="small"),
    }
    
    st.dataframe(
        df_display[['date', 'Điện Toán', 'tt_number', 'xsmb_full', 'g1_full']], 
        column_config=col_cfg, 
        hide_index=True, 
        use_container_width=True
    )

# === TAB 2: DÀN NUÔI ===
with tabs[1]:
    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        src_mode = st.selectbox("Nguồn tạo dàn:", ["Thần Tài", "Điện Toán"])
    with c2:
        comp_mode = st.selectbox("So sánh với:", ["XSMB (ĐB)", "Giải Nhất"])
    with c3:
        check_range = st.slider("Khung nuôi (ngày):", 1, 30, 21)
    
    if st.button("🚀 Phân Tích Dàn Nuôi"):
        res_list = []
        missed_info = []
        
        # Chuẩn bị dữ liệu cột so sánh
        col_comp = "xsmb_2so" if comp_mode == "XSMB (ĐB)" else "g1_2so"
        latest_val = df_full.iloc[0][col_comp] # Giá trị mới nhất để tô đỏ
        
        for i in range(len(df_show)):
            row_data = df_full.iloc[i]
            current_date = row_data['date']
            
            # Lấy số nguồn
            src_vals = []
            if src_mode == "Thần Tài" and row_data['tt_number']:
                src_vals = [row_data['tt_number']]
            elif src_mode == "Điện Toán" and isinstance(row_data['dt_numbers'], list):
                src_vals = ["".join(row_data['dt_numbers'])]
                
            if not src_vals: continue
            
            # Tạo dàn (Gộp tất cả số trong nguồn)
            digits = set("".join(src_vals))
            # Tạo tổ hợp 2 số
            combos = {a+b for a in digits for b in digits}
            
            # Check kết quả tương lai (Loop ngược về index 0)
            hits = 0
            k_cols = {}
            
            for k in range(1, check_range + 1):
                check_idx = i - k
                val_ref = ""
                if check_idx >= 0:
                    val_ref = df_full.iloc[check_idx][col_comp]
                
                status = val_ref if val_ref in combos else ""
                k_cols[f"{k}"] = status # Tên cột chỉ để số cho gọn
                if status: hits += 1
            
            r = {
                "Ngày": current_date,
                "Nguồn": src_vals[0],
                "Dàn": " ".join(sorted(combos)),
                "Status": "✅ ĂN" if hits > 0 else "⏳ CHỜ"
            }
            r.update(k_cols)
            res_list.append(r)
            
            # Logic thống kê dàn chưa nổ (chỉ tính trong 30 ngày đổ lại)
            if hits == 0 and i <= 30:
                 missed_info.extend(list(combos))

        if res_list:
            df_res = pd.DataFrame(res_list)
            
            def highlight_status(val):
                return 'background-color: #d4edda' if val == "✅ ĂN" else 'background-color: #f8d7da'
            
            st.dataframe(
                df_res.style.applymap(highlight_status, subset=['Status']),
                hide_index=True, use_container_width=True
            )
            
            # Thống kê mức số
            if missed_info:
                from collections import Counter
                st.divider()
                st.subheader("🔥 Thống Kê Mức Số (Dàn Chưa Ra)")
                counts = Counter(missed_info)
                
                # Group by frequency
                freq_dict = {}
                for num, freq in counts.items():
                    freq_dict.setdefault(freq, []).append(num)
                
                cols = st.columns(len(freq_dict) if len(freq_dict) < 5 else 5)
                sorted_freqs = sorted(freq_dict.keys(), reverse=True)
                
                for idx, freq in enumerate(sorted_freqs):
                    with cols[idx % 5]:
                        nums = sorted(freq_dict[freq])
                        # HTML tô đỏ số trùng với kết quả mới nhất
                        html_nums = []
                        for n in nums:
                            style = "color:red;font-weight:bold;border:1px solid red" if n == latest_val else "color:gray"
                            html_nums.append(f"<span style='{style}'>{n}</span>")
                        
                        st.markdown(f"**Mức {freq}** ({len(nums)} số)")
                        st.markdown(" ".join(html_nums), unsafe_allow_html=True)

# === TAB 3: BỆT CẦU ===
with tabs[2]:
    st.subheader("Soi Cầu Bệt")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        bet_source = st.selectbox("Nguồn xét bệt:", ["XSMB (ĐB)", "Giải Nhất", "Thần Tài"])
    with col_b2:
        bet_types = st.multiselect("Loại bệt:", ["Thẳng", "Bệt Phải", "Bệt trái"], default=["Thẳng", "Bệt Phải"])
    
    col_map = {"XSMB (ĐB)": "xsmb_full", "Giải Nhất": "g1_full", "Thần Tài": "tt_number"}
    sel_col = col_map[bet_source]
    
    bet_data = []
    for i in range(len(df_show) - 1):
        curr = str(df_show.iloc[i][sel_col])
        prev = str(df_show.iloc[i+1][sel_col]) # Ngày hôm trước (vì list sort date desc)
        
        if not curr or not prev or len(curr)<2 or len(prev)<2: continue
        
        # Tìm số bệt
        found = set()
        for t in bet_types:
            found.update(logic.tim_chu_so_bet(curr, prev, t))
            
        if found:
            # Tạo dàn đề xuất
            dan_cham = logic.lay_dan_cham(found)
            # Ghép nhị hợp với 2 số cuối ĐB hôm nay và hôm qua
            tail1 = df_full.iloc[i]['xsmb_2so']
            tail2 = df_full.iloc[i+1]['xsmb_2so']
            dan_nhi_hop = logic.lay_nhi_hop(found, tail1 + tail2)
            
            final_dan = sorted(set(dan_cham + dan_nhi_hop))
            
            # Check WIN (ngày mai - tức là index i-1)
            res_mai = "N/A"
            win_stt = ""
            if i > 0:
                res_mai = df_full.iloc[i-1]['xsmb_2so']
                win_stt = "🏆 WIN" if res_mai in final_dan else ""
            
            bet_data.append({
                "Ngày": df_show.iloc[i]['date'],
                "Nguồn (Hôm nay)": curr,
                "Nguồn (Hôm qua)": prev,
                "Số Bệt": ",".join(found),
                "Dàn Nuôi (cho mai)": " ".join(final_dan),
                "Kết Quả Mai": f"{res_mai} {win_stt}"
            })
            
    st.dataframe(pd.DataFrame(bet_data), use_container_width=True)

# === TAB 4: THỐNG KÊ LAST 2 ===
with tabs[3]:
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        df_l2 = pd.DataFrame()
        df_l2['Ngày'] = df_show['date']
        df_l2['ĐB'] = df_show['xsmb_2so']
        df_l2['Bộ'] = df_show['xsmb_2so'].apply(logic.bo)
        df_l2['Tổng'] = df_show['xsmb_2so'].apply(lambda x: (int(x[0])+int(x[1]))%10 if x and x.isdigit() else "")
        st.dataframe(df_l2, hide_index=True, use_container_width=True)
        
    with col_l2:
        st.write("📊 **Top Bộ Gan (Lâu chưa ra)**")
        # Tính gan trên toàn bộ dữ liệu tải về (df_full)
        all_tails = df_full['xsmb_2so'].dropna().tolist()
        
        last_seen_bo = {}
        for idx, val in enumerate(all_tails):
            if not val.isdigit(): continue
            b = logic.bo(val)
            if b not in last_seen_bo:
                last_seen_bo[b] = idx # idx 0 là hôm nay
                
        df_gan = pd.DataFrame(list(last_seen_bo.items()), columns=['Bộ', 'Số ngày chưa ra'])
        df_gan = df_gan.sort_values('Số ngày chưa ra', ascending=False).head(10)
        st.dataframe(df_gan, hide_index=True, use_container_width=True)

# === TAB 5: TRA CỨU ===
with tabs[4]:
    st.info("Nhập cặp số (ví dụ 68) để xem nó đã về những ngày nào ở Giải ĐB hoặc G1.")
    search_num = st.text_input("Nhập số:", max_chars=2)
    
    if search_num and len(search_num) == 2:
        # Tìm trong master data
        found = []
        for _, row in df_full.iterrows():
            if search_num in str(row['xsmb_full']):
                found.append({"Ngày": row['date'], "Giải": "ĐB", "Số đầy đủ": row['xsmb_full']})
            if search_num in str(row['g1_full']):
                found.append({"Ngày": row['date'], "Giải": "G1", "Số đầy đủ": row['g1_full']})
        
        if found:
            st.success(f"Tìm thấy {len(found)} lần xuất hiện.")
            st.dataframe(pd.DataFrame(found), use_container_width=True)
        else:
            st.warning("Chưa thấy xuất hiện trong dữ liệu đã tải.")
