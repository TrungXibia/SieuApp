import streamlit as st
import pandas as pd
import logic
import data_fetcher

# --- CẤU HÌNH GIAO DIỆN CHUẨN ---
st.set_page_config(
    page_title="SIÊU GÀ APP",
    page_icon="🐔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS NHẸ NHÀNG (CHỈ TỐI ƯU TAB) ---
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 4px 4px 0 0; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { background-color: #ffffff; border-top: 2px solid #ff4b4b; }
</style>
""", unsafe_allow_html=True)

# --- HÀM RÚT GỌN NGÀY (GIỮ NGUYÊN VÌ RẤT HỮU ÍCH) ---
def shorten_date(date_str):
    try:
        parts = date_str.split(" ")
        raw_date = parts[-1] 
        day_mon = raw_date[:5] 
        return day_mon
    except:
        return date_str

# --- QUẢN LÝ DỮ LIỆU ---
@st.cache_data(ttl=3600)
def load_all_data(num_days):
    dt = data_fetcher.fetch_dien_toan(num_days)
    tt = data_fetcher.fetch_than_tai(num_days)
    xsmb = data_fetcher.fetch_phoi_cau_xsmb(num_days, dt)
    g1 = data_fetcher.fetch_giai_nhat(num_days, dt)
    return dt, tt, xsmb, g1

# --- SIDEBAR ---
with st.sidebar:
    st.title("🐔 SIÊU GÀ TOOL")
    days_fetch = st.number_input("Tải dữ liệu (ngày)", 50, 365, 100, step=50)
    days_show = st.slider("Hiển thị (ngày)", 10, 100, 30)
    if st.button("🔄 Cập nhật dữ liệu"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Bản ổn định v2.0")

# --- LOAD DATA ---
try:
    with st.spinner("Đang tải dữ liệu..."):
        full_dt, full_tt, full_xsmb, full_g1 = load_all_data(days_fetch)
except Exception as e:
    st.error(f"Lỗi kết nối: {e}")
    st.stop()

# Cắt dữ liệu
dt_show = full_dt[:days_show]
tt_show = full_tt[:days_show]
xsmb_show = full_xsmb[:days_show]
g1_show = full_g1[:days_show]

# Hàm chuẩn bị dữ liệu hiển thị (Rút gọn ngày)
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

# --- MAIN TABS ---
tabs = st.tabs(["📊 Kết Quả", "🎯 Dàn Nuôi", "🎲 Bệt (Bet)", "📈 Thống Kê Last2", "🔍 Dò Cầu"])

# === TAB 1: KẾT QUẢ ===
with tabs[0]:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Điện Toán 123")
        if dt_disp:
            df_dt = pd.DataFrame(dt_disp)
            df_dt['Chuỗi số'] = df_dt['numbers'].apply(lambda x: " - ".join(x))
            st.dataframe(
                df_dt[['date', 'Chuỗi số']], 
                hide_index=True, 
                use_container_width=True,
                column_config={"date": "Ngày", "Chuỗi số": "Kết Quả"}
            )
    with c2:
        st.subheader("Thần Tài")
        if tt_disp:
            st.dataframe(pd.DataFrame(tt_disp), hide_index=True, use_container_width=True, column_config={"date":"Ngày", "number":"Số"})
    
    st.divider()
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("XSMB (GĐB)")
        if xsmb_disp:
            st.dataframe(pd.DataFrame(xsmb_disp), hide_index=True, use_container_width=True, column_config={"date":"Ngày", "number":"Số"})
    with c4:
        st.subheader("Giải Nhất (G1)")
        if g1_disp:
            st.dataframe(pd.DataFrame(g1_disp), hide_index=True, use_container_width=True, column_config={"date":"Ngày", "number":"Số"})

# === TAB 2: DÀN NUÔI (ĐÃ SỬA LẠI HIỂN THỊ CHUẨN) ===
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
                if check_idx >= 0:
                    val_ref = ref_data[check_idx]["number"][-2:]
                
                status = val_ref if val_ref in combos else ""
                k_cols[f"K{k}"] = status
                if status: hits += 1
            
            # Dùng ngày rút gọn
            row = {
                "Ngày": shorten_date(dt_show[i]['date']),
                "KQ Nguồn": val,
                "Dàn": " ".join(sorted(combos)),
                "Trạng thái": "Đã Nổ" if hits > 0 else "CHƯA NỔ"
            }
            row.update(k_cols)
            results.append(row)
            
            if hits == 0 and i <= 30: 
                missed_str = " ".join(sorted(combos))
                missed_patterns.append(f"📅 {shorten_date(dt_show[i]['date'])} (KQ: {val}): {missed_str}")
                raw_missed_data.append(missed_str)

        df_res = pd.DataFrame(results)
        
        def color_status(val):
            return f'background-color: {"#ffcccc" if val == "CHƯA NỔ" else "#ccffcc"}'

        if not df_res.empty:
            # Cấu hình cột chuẩn, không ép CSS
            col_config = {
                "Ngày": st.column_config.TextColumn("Ngày", width="small"),
                "KQ Nguồn": st.column_config.TextColumn("KQ", width="small"), 
                "Dàn": st.column_config.TextColumn("Dàn Nuôi", width="medium"),
                "Trạng thái": st.column_config.TextColumn("Trạng thái", width="small"),
            }
            
            # Cấu hình cột K
            for k_col in [c for c in df_res.columns if c.startswith("K")]:
                col_config[k_col] = st.column_config.TextColumn(
                    k_col.replace("K", ""), 
                    width="small"
                )

            st.dataframe(
                df_res.style.applymap(color_status, subset=['Trạng thái']),
                column_config=col_config,
                use_container_width=True, # Để True cho bảng tràn màn hình đẹp
                hide_index=True
            )
        
        if missed_patterns:
            st.divider()
            c_warn, c_stat = st.columns([1, 1])
            with c_warn:
                st.warning("⚠️ CẢNH BÁO: Các dàn chưa nổ (30 ngày gần nhất)")
                st.text_area("Chi tiết:", "\n".join(missed_patterns), height=300)
            
            with c_stat:
                st.info("📊 THỐNG KÊ MỨC SỐ")
                if raw_missed_data:
                    from collections import Counter
                    all_nums = " ".join(raw_missed_data).split()
                    counts = Counter(all_nums)
                    levels = {}
                    for num, freq in counts.items(): levels.setdefault(freq, []).append(num)
                    
                    for lvl in sorted(levels.keys(), reverse=True):
                        nums = sorted(levels[lvl])
                        disp = []
                        for n in nums:
                            if n == latest_ref_val:
                                disp.append(f"<span style='color:red; font-weight:bold; border:1px solid red; padding:2px'>{n}</span>")
                            else:
                                disp.append(n)
                        st.markdown(f"**Mức {lvl}** ({len(nums)} số): {', '.join(disp)}", unsafe_allow_html=True)
                    st.caption(f"*Số đỏ là trùng với KQ mới nhất ({latest_ref_val})*")

# === TAB 3: BỆT ===
with tabs[2]:
    st.header("Thống Kê Bệt")
    bet_src_name = st.selectbox("Nguồn Bệt:", ["GĐB", "G1", "Thần Tài"])
    bet_opts = st.multiselect("Kiểu Bệt:", ["Bệt Phải", "Thẳng", "Bệt trái"], default=["Bệt Phải", "Thẳng", "Bệt trái"])
    
    if bet_src_name == "GĐB": src_dat = xsmb_show
    elif bet_src_name == "G1": src_dat = g1_show
    else: src_dat = tt_show
    
    gdb_tails = [x['number'][-2:] for x in full_xsmb]
    
    bet_rows = []
    for i in range(len(src_dat)):
        curr_item = src_dat[i]
        next_item = src_dat[i+1] if i+1 < len(src_dat) else None
        if not next_item: continue
        
        d1 = list(curr_item['number'])
        d2 = list(next_item['number'])
        found_bet = set()
        for opt in bet_opts: found_bet.update(logic.tim_chu_so_bet(d1, d2, opt))
        
        if not found_bet: continue
        
        dancham = logic.lay_dan_cham(list(found_bet))
        t1 = gdb_tails[i] if i < len(gdb_tails) else ""
        t2 = gdb_tails[i+1] if i+1 < len(gdb_tails) else ""
        nhihop = logic.lay_nhi_hop(list(found_bet), list(t1)+list(t2))
        final_dan = sorted(set(dancham + nhihop))
        res_mai = gdb_tails[i-1] if i-1 >= 0 else "?"
        is_win = "WIN" if res_mai in final_dan else "-"
        
        bet_rows.append({
            "Ngày": shorten_date(curr_item['date']),
            "Nguồn": curr_item['number'],
            "Bệt": ",".join(sorted(found_bet)),
            "Dàn Nuôi": " ".join(final_dan),
            "KQ Mai": f"{res_mai} ({is_win})"
        })
    st.dataframe(pd.DataFrame(bet_rows), use_container_width=True, hide_index=True)

# === TAB 4: LAST 2 ===
with tabs[3]:
    st.header("Thống Kê 2 Số Cuối")
    l2_src = st.radio("Nguồn:", ["GĐB", "G1"], horizontal=True, key="l2")
    dat_l2 = full_xsmb if l2_src == "GĐB" else full_g1
    
    rows_l2 = []
    for x in dat_l2[:days_show]:
        n = x['number'][-2:]
        rows_l2.append({
            "Ngày": shorten_date(x['date']),
            "Số": n,
            "Bộ": logic.bo(n),
            "Tổng": (int(n[0])+int(n[1]))%10,
            "Kép": logic.kep(n)
        })
    st.dataframe(pd.DataFrame(rows_l2), use_container_width=True, hide_index=True)
    
    st.subheader("Top Bộ Số Lâu Chưa Ra")
    all_tails = [x['number'][-2:] for x in dat_l2]
    
    def analyze_gan(extractor):
        last_seen = {}
        for idx, val in enumerate(all_tails):
            k = extractor(val)
            if k not in last_seen: last_seen[k] = idx
        res = [{"Giá trị": k, "Số ngày chưa ra": v} for k,v in last_seen.items()]
        return pd.DataFrame(res).sort_values("Số ngày chưa ra", ascending=False).head(10)

    c1, c2 = st.columns(2)
    with c1:
        st.write("🔴 **Bộ Gan**")
        st.dataframe(analyze_gan(logic.bo), hide_index=True, use_container_width=True)
    with c2:
        st.write("🔵 **Tổng Gan**")
        st.dataframe(analyze_gan(lambda x: str((int(x[0])+int(x[1]))%10)), hide_index=True, use_container_width=True)

# === TAB 5: DÒ CẦU ===
with tabs[4]:
    st.header("Công Cụ Dò Cầu")
    target = st.text_input("Nhập cặp số muốn tìm (VD: 68):", max_chars=2)
    if target and len(target) == 2:
        found = []
        for x in full_xsmb[:days_fetch]:
            if target in x['number']: found.append({"Ngày": shorten_date(x['date']), "Nguồn": "GĐB", "Số": x['number']})
        for x in full_g1[:days_fetch]:
            if target in x['number']: found.append({"Ngày": shorten_date(x['date']), "Nguồn": "G1", "Số": x['number']})
        
        if found:
            st.success(f"Tìm thấy {len(found)} lần xuất hiện.")
            st.dataframe(pd.DataFrame(found), use_container_width=True, hide_index=True)
        else:
            st.warning("Không tìm thấy.")
