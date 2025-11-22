import streamlit as st
import pandas as pd
import logic
import data_fetcher

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(
    page_title="SIÊU GÀ APP - PRO",
    page_icon="🐔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS TÙY CHỈNH (Fix lỗi màu chữ menu & Tối ưu bảng) ---
st.markdown("""
<style>
    /* Tùy chỉnh Tab: Ép màu chữ đen để hiện rõ trên nền xám */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #e0e0e0; /* Nền xám nhạt */
        border-radius: 5px 5px 0 0;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #000000 !important; /* QUAN TRỌNG: Ép màu chữ đen */
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #ff4b4b !important; /* Màu đỏ cho tab đang chọn */
        color: #ffffff !important; /* Chữ trắng cho tab đang chọn */
        border-top: 2px solid #ff4b4b;
    }

    /* Tùy chỉnh bảng dataframe cho gọn */
    div[data-testid="stDataFrame"] { width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- 1. QUẢN LÝ DỮ LIỆU (CACHE) ---
@st.cache_data(ttl=3600) 
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
    st.caption("Giao diện mới: Bảng chéo tích ngày")
    st.markdown("---")
    days_fetch = st.number_input("Số ngày tải dữ liệu", 50, 365, 100, step=50)
    days_show = st.slider("Số ngày hiển thị", 10, 100, 30)
    
    if st.button("🔄 Cập nhật dữ liệu", type="primary"):
        st.cache_data.clear()
        st.rerun()

# --- LOAD DATA ---
try:
    with st.spinner("Đang tải dữ liệu..."):
        full_dt, full_tt, full_xsmb, full_g1 = load_all_data(days_fetch)
except Exception as e:
    st.error(f"Lỗi kết nối hoặc dữ liệu: {e}")
    st.stop()

# Cắt dữ liệu hiển thị
dt_show = full_dt[:days_show]
tt_show = full_tt[:days_show]
xsmb_show = full_xsmb[:days_show]
g1_show = full_g1[:days_show]

# --- 3. MAIN TABS ---
tabs = st.tabs(["📊 KẾT QUẢ", "🎯 DÀN NUÔI", "🎲 BỆT (BET)", "📈 THỐNG KÊ L2", "🔍 DÒ CẦU"])

# === TAB 1: KẾT QUẢ ===
with tabs[0]:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Điện Toán 123")
        if dt_show:
            df_dt = pd.DataFrame(dt_show)
            df_dt['Chuỗi số'] = df_dt['numbers'].apply(lambda x: " - ".join(x))
            st.dataframe(df_dt[['date', 'Chuỗi số']], hide_index=True, use_container_width=True)
    with c2:
        st.markdown("##### Thần Tài")
        if tt_show:
            st.dataframe(pd.DataFrame(tt_show), hide_index=True, use_container_width=True)
    
    st.divider()
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("##### XSMB (GĐB)")
        if xsmb_show:
            st.dataframe(pd.DataFrame(xsmb_show), hide_index=True, use_container_width=True)
    with c4:
        st.markdown("##### Giải Nhất (G1)")
        if g1_show:
            st.dataframe(pd.DataFrame(g1_show), hide_index=True, use_container_width=True)

# === TAB 2: DÀN NUÔI (ĐÃ SỬA BẢNG CHÉO) ===
with tabs[1]:
    st.markdown("### 🎯 Phân Tích Hiệu Quả Dàn Nuôi (Dạng Bảng)")
    
    # Control Panel
    with st.container():
        c_ctrl1, c_ctrl2, c_ctrl3 = st.columns([1, 1, 2])
        with c_ctrl1:
            res_type = st.selectbox("Nguồn lấy số:", ["Thần tài", "Điện toán"])
        with c_ctrl2:
            source_comp = st.selectbox("So sánh với:", ["GĐB", "G1"])
        with c_ctrl3:
            check_range = st.slider("Khung nuôi (ngày):", 3, 25, 10)

    if st.button("🚀 Chạy Phân Tích", type="primary"):
        source_list = [x["number"] for x in tt_show] if res_type == "Thần tài" else ["".join(x["numbers"]) for x in dt_show]
        ref_data = full_xsmb if source_comp == "GĐB" else full_g1
        
        results = []
        
        # Loop xử lý
        for i in range(len(source_list)):
            val = source_list[i]
            digits = list(val)
            
            # Tạo dàn (Bao gồm cả kép)
            combos = {a+b for a in digits for b in digits}
            if not combos: continue

            # Check khung ngày
            k_cols = {}
            hits = 0
            first_hit_day = ""
            
            for k in range(1, check_range + 1):
                check_idx = i - k
                col_name = f"{k}" # Tên cột ngắn gọn: 1, 2, 3... thay vì K1, K2
                
                val_ref = ""
                if check_idx >= 0:
                    val_ref = ref_data[check_idx]["number"][-2:]
                
                if val_ref and val_ref in combos:
                    hits += 1
                    k_cols[col_name] = f"✅ {val_ref}" # Đánh dấu tích + số trúng
                    if not first_hit_day: first_hit_day = f"N{k}"
                else:
                    k_cols[col_name] = "" # Ô trống cho dễ nhìn
            
            row = {
                "Ngày": dt_show[i]['date'],
                "Nguồn": val,
                "Dàn": f"{len(combos)} số", # Rút gọn hiển thị dàn cho đỡ rối
                "Kết quả": f"Ăn {first_hit_day}" if hits > 0 else "⏳",
            }
            row.update(k_cols)
            results.append(row)

        df_res = pd.DataFrame(results)
        
        if not df_res.empty:
            # --- TẠO BẢNG CHÉO ĐẸP ---
            
            # 1. Định nghĩa cột để hiển thị gọn
            col_cfg = {
                "Ngày": st.column_config.TextColumn("Ngày", width="small"),
                "Nguồn": st.column_config.TextColumn("Nguồn", width="small"),
                "Dàn": st.column_config.TextColumn("SL", width="small"),
                "Kết quả": st.column_config.TextColumn("Tổng kết", width="small"),
            }
            
            # Cấu hình các cột ngày K (1, 2, 3...) cho nhỏ lại
            k_columns = [str(k) for k in range(1, check_range + 1)]
            for k in k_columns:
                col_cfg[k] = st.column_config.TextColumn(
                    f"N{k}", # Header hiển thị là N1, N2...
                    width="small" 
                )

            # 2. Hàm tô màu nền (Highlight)
            def highlight_hits(val):
                # Tô màu xanh lá cho ô trúng
                if "✅" in str(val):
                    return 'background-color: #d4edda; color: #155724; font-weight: bold; text-align: center;'
                return ''

            def highlight_status(val):
                if "Ăn" in str(val):
                    return 'background-color: #c3e6cb; color: darkgreen; font-weight: bold;'
                return 'background-color: #f8d7da; color: #721c24;'

            # 3. Hiển thị Dataframe với Styler
            st.dataframe(
                df_res.style
                      .applymap(highlight_hits, subset=k_columns)
                      .applymap(highlight_status, subset=['Kết quả']),
                column_config=col_cfg,
                use_container_width=True,
                hide_index=True
            )
            
            st.caption("*Ghi chú: N1, N2... là ngày thứ 1, thứ 2 nuôi. Ô màu xanh là trúng số đó.*")

# === TAB 3: BỆT (BET) ===
with tabs[2]:
    st.markdown("### 🎲 Soi Cầu Bệt")
    
    c_b1, c_b2 = st.columns(2)
    with c_b1:
        bet_src_name = st.selectbox("Nguồn Bệt:", ["GĐB", "G1", "Thần Tài"])
    with c_b2:
        bet_opts = st.multiselect("Kiểu Bệt:", ["Bệt Phải", "Thẳng", "Bệt trái"], default=["Bệt Phải", "Thẳng"])
    
    if bet_src_name == "GĐB": src_dat = xsmb_show
    elif bet_src_name == "G1": src_dat = g1_show
    else: src_dat = tt_show
    
    gdb_tails = [x['number'][-2:] for x in full_xsmb]
    
    bet_rows = []
    for i in range(len(src_dat)):
        curr_item = src_dat[i]
        next_item = src_dat[i+1] if i+1 < len(src_dat) else None
        
        if not next_item: continue
        
        d1, d2 = list(curr_item['number']), list(next_item['number'])
        
        found_bet = set()
        for opt in bet_opts:
            found_bet.update(logic.tim_chu_so_bet(d1, d2, opt))
        
        if found_bet:
            dancham = logic.lay_dan_cham(list(found_bet))
            t1 = gdb_tails[i] if i < len(gdb_tails) else ""
            t2 = gdb_tails[i+1] if i+1 < len(gdb_tails) else ""
            nhihop = logic.lay_nhi_hop(list(found_bet), list(t1)+list(t2))
            
            final_dan = sorted(set(dancham + nhihop))
            
            res_mai = gdb_tails[i-1] if i-1 >= 0 else "?"
            is_win = "🏆 WIN" if res_mai in final_dan else "-"
            
            bet_rows.append({
                "Ngày": curr_item['date'],
                "Nguồn (Hôm nay)": curr_item['number'],
                "Số Bệt": ",".join(sorted(found_bet)),
                "Dàn Đề Xuất": " ".join(final_dan),
                "Kết Quả Mai": f"{res_mai} ({is_win})"
            })
        
    st.dataframe(pd.DataFrame(bet_rows), use_container_width=True)

# === TAB 4: LAST 2 ===
with tabs[3]:
    st.markdown("### 📈 Thống Kê 2 Số Cuối")
    l2_src = st.radio("Nguồn dữ liệu:", ["GĐB", "G1"], horizontal=True)
    dat_l2 = full_xsmb if l2_src == "GĐB" else full_g1
    
    c_stat1, c_stat2 = st.columns([2, 1])
    
    with c_stat1:
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
        st.dataframe(pd.DataFrame(rows_l2), use_container_width=True, hide_index=True)
    
    with c_stat2:
        st.info("🔴 **TOP BỘ GAN**")
        all_tails = [x['number'][-2:] for x in dat_l2]
        
        last_seen = {}
        for idx, val in enumerate(all_tails):
            k = logic.bo(val)
            if k not in last_seen: last_seen[k] = idx
        
        df_gan = pd.DataFrame([{"Bộ": k, "Số ngày": v} for k,v in last_seen.items()])
        df_gan = df_gan.sort_values("Số ngày", ascending=False).head(10)
        st.dataframe(df_gan, hide_index=True, use_container_width=True)

# === TAB 5: DÒ CẦU ===
with tabs[4]:
    st.markdown("### 🔍 Tra Cứu Lịch Sử Cầu")
    target = st.text_input("Nhập số muốn tìm (VD: 68):", max_chars=2)
    
    if target and len(target) == 2:
        found = []
        for x in full_xsmb[:days_fetch]:
            if target in x['number']: found.append({"Ngày": x['date'], "Giải": "GĐB", "Số đầy đủ": x['number']})
        for x in full_g1[:days_fetch]:
            if target in x['number']: found.append({"Ngày": x['date'], "Giải": "G1", "Số đầy đủ": x['number']})
        
        if found:
            st.success(f"Tìm thấy {len(found)} lần xuất hiện.")
            st.dataframe(pd.DataFrame(found), use_container_width=True)
        else:
            st.warning("Chưa thấy số này xuất hiện trong dữ liệu đã tải.")
