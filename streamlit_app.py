import streamlit as st
import pandas as pd
import logic
import data_fetcher

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(
    page_title="SIÊU GÀ APP - ONLINE",
    page_icon="🐔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS TÙY CHỈNH ---
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 4px 4px 0 0; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { background-color: #ffffff; border-top: 2px solid #ff4b4b; }
</style>
""", unsafe_allow_html=True)

# --- 1. QUẢN LÝ DỮ LIỆU (CACHE) ---
@st.cache_data(ttl=3600) # Cache 1 tiếng
def load_all_data(num_days):
    dt = data_fetcher.fetch_dien_toan(num_days)
    tt = data_fetcher.fetch_than_tai(num_days)
    # XSMB và G1 cần dữ liệu Điện Toán để lấy ngày
    xsmb = data_fetcher.fetch_phoi_cau_xsmb(num_days, dt)
    g1 = data_fetcher.fetch_giai_nhat(num_days, dt)
    return dt, tt, xsmb, g1

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("🐔 SIÊU GÀ TOOL")
    st.markdown("---")
    days_fetch = st.number_input("Số ngày tải dữ liệu", 50, 365, 100, step=50)
    days_show = st.slider("Số ngày hiển thị", 10, 100, 30)
    
    if st.button("🔄 Cập nhật dữ liệu mới nhất"):
        st.cache_data.clear()
        st.rerun()
    
    st.caption("Phiên bản Web v1.0")

# --- LOAD DATA ---
try:
    with st.spinner("Đang tải dữ liệu từ server..."):
        full_dt, full_tt, full_xsmb, full_g1 = load_all_data(days_fetch)
except Exception as e:
    st.error(f"Lỗi kết nối: {e}")
    st.stop()

# Cắt dữ liệu hiển thị
dt_show = full_dt[:days_show]
tt_show = full_tt[:days_show]
xsmb_show = full_xsmb[:days_show]
g1_show = full_g1[:days_show]

# --- 3. MAIN TABS ---
tabs = st.tabs(["📊 Kết Quả", "🎯 Dàn Nuôi", "🎲 Bệt (Bet)", "📈 Thống Kê Last2", "🔍 Dò Cầu"])

# === TAB 1: KẾT QUẢ ===
with tabs[0]:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Điện Toán 123")
        if dt_show:
            df_dt = pd.DataFrame(dt_show)
            # Tách mảng numbers thành chuỗi
            df_dt['Chuỗi số'] = df_dt['numbers'].apply(lambda x: " - ".join(x))
            st.dataframe(df_dt[['date', 'Chuỗi số']], hide_index=True, use_container_width=True)
    with c2:
        st.subheader("Thần Tài")
        if tt_show:
            st.dataframe(pd.DataFrame(tt_show), hide_index=True, use_container_width=True)
    
    st.divider()
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("XSMB (GĐB)")
        if xsmb_show:
            st.dataframe(pd.DataFrame(xsmb_show), hide_index=True, use_container_width=True)
    with c4:
        st.subheader("Giải Nhất (G1)")
        if g1_show:
            st.dataframe(pd.DataFrame(g1_show), hide_index=True, use_container_width=True)

# === TAB 2: DÀN NUÔI ===
with tabs[1]:
    st.header("Phân Tích Dàn Nuôi")
    col_ctrl1, col_ctrl2 = st.columns(2)
    with col_ctrl1:
        source_comp = st.radio("So sánh với:", ["GĐB", "G1"], horizontal=True)
        res_type = st.selectbox("Nguồn tạo dàn:", ["Thần tài", "Điện toán"])
    with col_ctrl2:
        cham_filter = st.selectbox("Lọc chạm (Optional):", [""] + [str(i) for i in range(10)])
        include_dup = st.checkbox("Bao gồm số trùng (Kép)", value=True)

    if st.button("🚀 Phân Tích Ngay"):
        # Chọn nguồn dữ liệu
        source_list = [x["number"] for x in tt_show] if res_type == "Thần tài" else ["".join(x["numbers"]) for x in dt_show]
        ref_data = full_xsmb if source_comp == "GĐB" else full_g1
        
        results = []
        missed_patterns = [] # Dàn chưa ra

        for i in range(len(source_list)):
            val = source_list[i]
            digits = list(val)
            
            # Tạo dàn
            combos = {a+b for a in digits for b in digits}
            if not include_dup: combos = {c for c in combos if c[0] != c[1]}
            if cham_filter: combos = {c for c in combos if cham_filter in c}
            
            if not combos: continue

            # Kiểm tra kết quả (21 ngày tiếp theo - tức là index nhỏ hơn trong list)
            # Lưu ý: List đang sort Mới -> Cũ. i là hiện tại.
            # Check xem dàn này có nổ ở các ngày SAU đó không (index < i)
            
            check_range = 21 # Khung nuôi
            k_cols = {}
            hits = 0
            
            for k in range(1, check_range + 1):
                check_idx = i - k
                val_ref = ""
                if check_idx >= 0:
                    val_ref = ref_data[check_idx]["number"][-2:] # 2 số cuối
                
                status = val_ref if val_ref in combos else ""
                k_cols[f"K{k}"] = status
                if status: hits += 1
            
            row = {
                "Ngày": dt_show[i]['date'],
                "KQ Nguồn": val,
                "Dàn": " ".join(sorted(combos)),
                "Trạng thái": "Đã Nổ" if hits > 0 else "CHƯA NỔ"
            }
            row.update(k_cols)
            results.append(row)
            
            if hits == 0 and i <= 30: # Chỉ báo động các ngày gần đây
                missed_patterns.append(f"{dt_show[i]['date']} ({val}): " + " ".join(sorted(combos)))

        df_res = pd.DataFrame(results)
        
        # Hiển thị
        def color_status(val):
            color = '#ffcccc' if val == "CHƯA NỔ" else '#ccffcc'
            return f'background-color: {color}'

        if not df_res.empty:
            st.dataframe(df_res.style.applymap(color_status, subset=['Trạng thái']), use_container_width=True)
        
        if missed_patterns:
            st.warning("⚠️ CẢNH BÁO: Các dàn đang nuôi chưa nổ (Khung 21 ngày gần nhất):")
            st.text("\n".join(missed_patterns))

# === TAB 3: BỆT (BET) ===
with tabs[2]:
    st.header("Thống Kê Bệt")
    
    bet_src_name = st.selectbox("Nguồn Bệt:", ["GĐB", "G1", "Thần Tài"])
    bet_opts = st.multiselect("Kiểu Bệt:", ["Bệt Phải", "Thẳng", "Bệt trái"], default=["Bệt Phải", "Thẳng", "Bệt trái"])
    
    if bet_src_name == "GĐB": src_dat = xsmb_show
    elif bet_src_name == "G1": src_dat = g1_show
    else: src_dat = tt_show
    
    # Dữ liệu đối chiếu (2 số cuối GĐB)
    gdb_tails = [x['number'][-2:] for x in full_xsmb]
    
    bet_rows = []
    for i in range(len(src_dat)):
        curr_item = src_dat[i]
        next_item = src_dat[i+1] if i+1 < len(src_dat) else None
        
        if not next_item: continue
        
        d1 = list(curr_item['number'])
        d2 = list(next_item['number'])
        
        found_bet = set()
        for opt in bet_opts:
            found_bet.update(logic.tim_chu_so_bet(d1, d2, opt))
        
        if not found_bet: continue # Bỏ qua nếu không có bệt
        
        # Tạo dàn nuôi
        dancham = logic.lay_dan_cham(list(found_bet))
        
        # Nhị hợp 2 số cuối GĐB hiện tại và hôm qua
        t1 = gdb_tails[i] if i < len(gdb_tails) else ""
        t2 = gdb_tails[i+1] if i+1 < len(gdb_tails) else ""
        nhihop = logic.lay_nhi_hop(list(found_bet), list(t1)+list(t2))
        
        final_dan = sorted(set(dancham + nhihop))
        
        # Check kết quả ngày mai (i-1)
        res_mai = gdb_tails[i-1] if i-1 >= 0 else "?"
        is_win = "WIN" if res_mai in final_dan else "-"
        
        bet_rows.append({
            "Ngày": curr_item['date'],
            "Nguồn": curr_item['number'],
            "Bệt": ",".join(sorted(found_bet)),
            "Dàn Nuôi": " ".join(final_dan),
            "KQ Mai": f"{res_mai} ({is_win})"
        })
        
    st.dataframe(pd.DataFrame(bet_rows), use_container_width=True)

# === TAB 4: LAST 2 ===
with tabs[3]:
    st.header("Thống Kê 2 Số Cuối")
    l2_src = st.radio("Nguồn:", ["GĐB", "G1"], horizontal=True, key="l2_k")
    dat_l2 = full_xsmb if l2_src == "GĐB" else full_g1
    
    # Bảng chi tiết
    rows_l2 = []
    for x in dat_l2[:days_show]:
        n = x['number'][-2:]
        rows_l2.append({
            "Ngày": x['date'],
            "Số": n,
            "Bộ": logic.bo(n),
            "Tổng": (int(n[0])+int(n[1]))%10,
            "Kép": logic.kep(n)
        })
    st.dataframe(pd.DataFrame(rows_l2), use_container_width=True)
    
    # Thống kê GAN (Lâu ra)
    st.subheader("Top Bộ Số Lâu Chưa Ra (Toàn bộ dữ liệu tải về)")
    all_tails = [x['number'][-2:] for x in dat_l2] # Lấy hết data đã tải
    
    def analyze_gan(extractor, label):
        last_seen = {}
        for idx, val in enumerate(all_tails):
            k = extractor(val)
            if k not in last_seen:
                last_seen[k] = idx # idx càng nhỏ là càng mới
        
        res = [{"Giá trị": k, "Số ngày chưa ra": v} for k,v in last_seen.items()]
        df = pd.DataFrame(res).sort_values("Số ngày chưa ra", ascending=False).head(10)
        return df

    c_gan1, c_gan2 = st.columns(2)
    with c_gan1:
        st.write("🔴 **Bộ Gan**")
        st.dataframe(analyze_gan(logic.bo, "Bộ"), hide_index=True)
    with c_gan2:
        st.write("🔵 **Tổng Gan**")
        st.dataframe(analyze_gan(lambda x: str((int(x[0])+int(x[1]))%10), "Tổng"), hide_index=True)

# === TAB 5: DÒ CẦU ===
with tabs[4]:
    st.header("Công Cụ Dò Cầu")
    target = st.text_input("Nhập cặp số muốn tìm (VD: 68):", max_chars=2)
    
    if target and len(target) == 2:
        found = []
        # Tìm trong GĐB
        for x in full_xsmb[:days_fetch]:
            if target in x['number']:
                found.append({"Ngày": x['date'], "Nguồn": "GĐB", "Số": x['number']})
        # Tìm trong G1
        for x in full_g1[:days_fetch]:
            if target in x['number']:
                found.append({"Ngày": x['date'], "Nguồn": "G1", "Số": x['number']})
        
        if found:
            st.success(f"Tìm thấy {len(found)} lần xuất hiện.")
            st.dataframe(pd.DataFrame(found), use_container_width=True)
        else:
            st.warning("Không tìm thấy trong phạm vi dữ liệu.")