import streamlit as st
import pandas as pd
import logic
import data_fetcher
from collections import Counter

# ==============================================================================
# 1. CẤU HÌNH & CSS
# ==============================================================================
st.set_page_config(
    page_title="SIÊU GÀ APP",
    page_icon="🐔",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] { 
        height: 40px; 
        padding: 5px 10px;
        font-size: 14px;
        background-color: #f0f2f6; 
        border-radius: 4px 4px 0 0; 
    }
    .stTabs [aria-selected="true"] { 
        background-color: #ffffff; 
        border-top: 2px solid #ff4b4b; 
    }
    /* Thu nhỏ padding bảng để hiển thị nhiều cột */
    div[data-testid="stDataFrame"] td, div[data-testid="stDataFrame"] th {
        padding: 2px 4px !important;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. HÀM HỖ TRỢ & DATA
# ==============================================================================
def shorten_date(date_str):
    try:
        parts = date_str.split(" ")
        return parts[-1][:5]
    except:
        return date_str

@st.cache_data(ttl=3600)
def load_all_data(num_days):
    dt = data_fetcher.fetch_dien_toan(num_days)
    tt = data_fetcher.fetch_than_tai(num_days)
    xsmb = data_fetcher.fetch_phoi_cau_xsmb(num_days, dt)
    g1 = data_fetcher.fetch_giai_nhat(num_days, dt)
    return dt, tt, xsmb, g1

with st.sidebar:
    st.title("🐔 SIÊU GÀ TOOL")
    days_fetch = st.number_input("Tải dữ liệu (ngày)", 50, 365, 100, step=50)
    days_show = st.slider("Hiển thị (ngày)", 10, 60, 30)
    if st.button("🔄 Cập nhật dữ liệu"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Phiên bản v6.0 (Thêm Tab Tần Suất)")

try:
    with st.spinner("Đang tải dữ liệu..."):
        full_dt, full_tt, full_xsmb, full_g1 = load_all_data(days_fetch)
except Exception as e:
    st.error(f"Lỗi kết nối: {e}")
    st.stop()

dt_show = full_dt[:days_show]
tt_show = full_tt[:days_show]
xsmb_show = full_xsmb[:days_show]
g1_show = full_g1[:days_show]

# ==============================================================================
# 3. GIAO DIỆN CHÍNH (TABS)
# ==============================================================================
# ĐÃ THÊM TAB 6: TẦN SUẤT
tabs = st.tabs(["📊 Kết Quả", "🎯 Dàn Nuôi", "🎲 Bệt (Bet)", "📈 Thống Kê & Copy", "🔍 Dò Cầu", "🔢 Tần Suất"])

# --- TAB 1: KẾT QUẢ ---
with tabs[0]:
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Điện Toán 123")
        if dt_show:
            df_dt = pd.DataFrame(dt_show).copy()
            df_dt['date'] = df_dt['date'].apply(shorten_date)
            df_dt['Chuỗi số'] = df_dt['numbers'].apply(lambda x: " - ".join(x))
            st.dataframe(df_dt[['date', 'Chuỗi số']], hide_index=True, use_container_width=True, 
                         column_config={"date": st.column_config.TextColumn("Ngày", width="small")})
    with c2:
        st.caption("Thần Tài")
        if tt_show:
            df_tt = pd.DataFrame(tt_show).copy()
            df_tt['date'] = df_tt['date'].apply(shorten_date)
            st.dataframe(df_tt, hide_index=True, use_container_width=True,
                         column_config={"date": st.column_config.TextColumn("Ngày", width="small"), "number":"Số"})
    st.divider()
    c3, c4 = st.columns(2)
    with c3:
        st.caption("XSMB (GĐB)")
        if xsmb_show:
            df_xs = pd.DataFrame(xsmb_show).copy()
            df_xs['date'] = df_xs['date'].apply(shorten_date)
            st.dataframe(df_xs, hide_index=True, use_container_width=True,
                         column_config={"date": st.column_config.TextColumn("Ngày", width="small"), "number":"Số"})
    with c4:
        st.caption("Giải Nhất (G1)")
        if g1_show:
            df_g1 = pd.DataFrame(g1_show).copy()
            df_g1['date'] = df_g1['date'].apply(shorten_date)
            st.dataframe(df_g1, hide_index=True, use_container_width=True,
                         column_config={"date": st.column_config.TextColumn("Ngày", width="small"), "number":"Số"})

# --- TAB 2: DÀN NUÔI ---
with tabs[1]:
    st.caption("Phân Tích Dàn Nuôi & Mức Số")
    c_src, c_type, c_filt = st.columns([1,1,2])
    source_comp = c_src.radio("So sánh:", ["GĐB", "G1"], horizontal=True)
    res_type = c_type.selectbox("Nguồn:", ["Thần tài", "Điện toán"])
    cham_filter = c_filt.selectbox("Lọc chạm:", [""] + [str(i) for i in range(10)])
    include_dup = st.checkbox("Bao gồm số trùng (Kép)", value=True)

    if st.button("🚀 Phân Tích Dàn"):
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
            
            row = {
                "Ngày": shorten_date(dt_show[i]['date']),
                "KQ": val,
                "Dàn": " ".join(sorted(combos)),
                "TT": "NO" if hits > 0 else "MISS"
            }
            row.update(k_cols)
            results.append(row)
            
            if hits == 0 and i < 21: 
                missed_str = " ".join(sorted(combos))
                missed_patterns.append(f"📅 {shorten_date(dt_show[i]['date'])} ({val}): {missed_str}")
                raw_missed_data.append(missed_str)

        df_res = pd.DataFrame(results)
        def color_status(val): return f'background-color: {"#ffcccc" if val == "MISS" else "#ccffcc"}'

        if not df_res.empty:
            col_config = {
                "Ngày": st.column_config.TextColumn("Ngày", width="small"),
                "KQ": st.column_config.TextColumn("KQ", width="small"), 
                "Dàn": st.column_config.TextColumn("Dàn Nuôi", width="medium"),
                "TT": st.column_config.TextColumn("TT", width="small"),
            }
            for k_col in [c for c in df_res.columns if c.startswith("K")]:
                col_config[k_col] = st.column_config.TextColumn(k_col.replace("K", ""), width="small")

            st.dataframe(df_res.style.applymap(color_status, subset=['TT']), column_config=col_config, use_container_width=True, hide_index=True)
        
        if missed_patterns:
            st.divider()
            c_warn, c_stat = st.columns([1, 1])
            with c_warn:
                st.warning("⚠️ CẢNH BÁO: Dàn chưa nổ (21 ngày gần nhất)")
                st.text_area("Chi tiết:", "\n".join(missed_patterns), height=300)
            with c_stat:
                st.info("📊 THỐNG KÊ MỨC SỐ")
                if raw_missed_data:
                    all_nums = " ".join(raw_missed_data).split()
                    counts = Counter(all_nums)
                    levels = {}
                    for num, freq in counts.items(): levels.setdefault(freq, []).append(num)
                    
                    for lvl in sorted(levels.keys(), reverse=True):
                        nums = sorted(levels[lvl])
                        disp = [f"<span style='color:red; font-weight:bold; border:1px solid red; padding:2px'>{n}</span>" if n==latest_ref_val else n for n in nums]
                        st.markdown(f"**Mức {lvl}** ({len(nums)} số): {', '.join(disp)}", unsafe_allow_html=True)
                    st.caption(f"*Số đỏ: Trùng với GĐB/G1 mới nhất ({latest_ref_val})*")

# --- TAB 3: BỆT ---
with tabs[2]:
    st.markdown("""
    <style>
        div[data-testid="stDataFrame"] { font-size: 12px !important; }
        div[data-testid="stDataFrame"] th, div[data-testid="stDataFrame"] td { padding: 2px 1px !important; }
        div[class*="stDataFrame"] div[role="columnheader"] { min-width: 10px !important; max-width: 30px !important; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        c_cfg1, c_cfg2 = st.columns([1, 3])
        with c_cfg1:
            target_src = st.selectbox("Nguồn phân tích (Bảng trái):", ["GĐB", "G1", "Thần Tài"], index=0)
        with c_cfg2:
            st.write("Kiểu bệt:")
            c_b1, c_b2, c_b3 = st.columns(3)
            use_phai = c_b1.checkbox("Bệt Phải", value=True)
            use_thang = c_b2.checkbox("Thẳng", value=True)
            use_trai = c_b3.checkbox("Bệt Trái", value=True)
            bet_types = []
            if use_phai: bet_types.append("Bệt Phải")
            if use_thang: bet_types.append("Thẳng")
            if use_trai: bet_types.append("Bệt trái")

    st.divider()
    gdb_tails = [x['number'][-2:] for x in full_xsmb]

    def create_detail_df(source_name, b_types):
        if source_name == "GĐB": src_data = xsmb_show
        elif source_name == "G1": src_data = g1_show
        else: src_data = tt_show
        
        rows = []
        for i in range(len(src_data)-1):
            curr, nxt = src_data[i], src_data[i+1]
            nums = list(curr['number'])
            if len(nums) < 5: nums = ['']*(5-len(nums)) + nums
            else: nums = nums[-5:]
            
            found = set()
            for t in b_types:
                found.update(logic.tim_chu_so_bet(list(curr['number']), list(nxt['number']), t))
            
            final_dan = []
            if found:
                dancham = logic.lay_dan_cham(list(found))
                t1 = gdb_tails[i] if i < len(gdb_tails) else ""
                t2 = gdb_tails[i+1] if i+1 < len(gdb_tails) else ""
                nhihop = logic.lay_nhi_hop(list(found), list(t1)+list(t2))
                final_dan = sorted(set(dancham + nhihop))

            check_cols = {}
            has_win_row = False
            for k in range(1, 16):
                chk_idx = i - k
                val_chk = "0"
                if chk_idx >= 0:
                    res = gdb_tails[chk_idx]
                    if final_dan and res in final_dan:
                        val_chk = "1"
                        has_win_row = True
                else:
                    val_chk = ""
                check_cols[f"F{k}"] = val_chk

            row_item = {
                "date": shorten_date(curr['date']),
                "A": nums[0], "B": nums[1], "C": nums[2], "D": nums[3], "E": nums[4],
                "N1": curr['number'][-2:],
                "Chạm": "".join(sorted(found)),
                "Bet": ",".join(sorted(found)),
                "Dàn": " ".join(final_dan) if final_dan else "",
                "WIN": has_win_row
            }
            row_item.update(check_cols)
            rows.append(row_item)
        return pd.DataFrame(rows)

    def create_summary_df(b_types):
        srcs = [("ĐB", xsmb_show), ("G1", g1_show), ("TT", tt_show)]
        rows = []
        for i in range(len(xsmb_show)-1):
            item = {"date": shorten_date(xsmb_show[i]['date'])}
            for name, data in srcs:
                curr, nxt = data[i], data[i+1]
                found = set()
                for t in b_types:
                    found.update(logic.tim_chu_so_bet(list(curr['number']), list(nxt['number']), t))
                item[name] = ",".join(sorted(found))
            rows.append(item)
        return pd.DataFrame(rows)

    col_left, col_right = st.columns([7, 3]) 

    with col_left:
        st.caption(f"📋 Chi tiết ({target_src})")
        df_detail = create_detail_df(target_src, bet_types)
        if not df_detail.empty:
            def highlight_win(row):
                c = 'color: red; font-weight: bold;' if row['WIN'] else ''
                return [c]*len(row)
            cfg_left = {
                "date": st.column_config.TextColumn("N", width="small"),
                "Dàn": st.column_config.TextColumn("Dàn", width="large"),
                "WIN": None
            }
            small_cols = ["A", "B", "C", "D", "E", "N1", "Chạm", "Bet"] + [f"F{k}" for k in range(1, 16)]
            for col in small_cols:
                label = col.replace("F", "") if col.startswith("F") else col
                cfg_left[col] = st.column_config.TextColumn(label, width="small")
            st.dataframe(df_detail.style.apply(highlight_win, axis=1), column_config=cfg_left, hide_index=True, use_container_width=False, height=600)

    with col_right:
        st.caption("📑 Tổng hợp")
        df_summ = create_summary_df(bet_types)
        if not df_summ.empty:
            cfg_right = {
                "date": st.column_config.TextColumn("Ngày", width="small"),
                "ĐB": st.column_config.TextColumn("ĐB", width="small"),
                "G1": st.column_config.TextColumn("G1", width="small"),
                "TT": st.column_config.TextColumn("TT", width="small"),
            }
            st.dataframe(df_summ, column_config=cfg_right, hide_index=True, use_container_width=False, height=600)

# --- TAB 4: THỐNG KÊ ---
with tabs[3]:
    st.caption("Thống Kê Top Lâu Ra & Tạo Mẫu Copy")
    l2_src = st.radio("Nguồn:", ["GĐB", "G1"], horizontal=True, key="l2_src_radio")
    dat_l2 = full_xsmb if l2_src == "GĐB" else full_g1
    all_tails = [x['number'][-2:] for x in dat_l2]

    def find_top_gan(data_list, extract_func, label, get_dan_func):
        last_seen = {}
        for idx, val in enumerate(data_list):
            k = extract_func(val)
            if k not in last_seen: last_seen[k] = idx
        if not last_seen: return None
        top_val = max(last_seen, key=last_seen.get)
        return {
            "Loại": label, "Giá trị": top_val, "Số ngày": last_seen[top_val],
            "Chữ": logic.doc_so_chu(last_seen[top_val]), "Dàn": get_dan_func(top_val)
        }

    stats = []
    stats.append(find_top_gan(all_tails, logic.bo, "Bộ", logic.get_bo_dan))
    stats.append(find_top_gan(all_tails, lambda x: x[0], "Đầu", logic.get_dau_dan))
    stats.append(find_top_gan(all_tails, lambda x: x[1], "Đuôi", logic.get_duoi_dan))
    stats.append(find_top_gan(all_tails, lambda x: str((int(x[0])+int(x[1]))%10), "Tổng", logic.get_tong_dan))
    stats.append(find_top_gan(all_tails, logic.hieu, "Hiệu", logic.get_hieu_dan))
    stats.append(find_top_gan(all_tails, logic.zodiac, "Con Giáp", logic.get_zodiac_dan))
    stats.append(find_top_gan(all_tails, logic.kep, "Kép", logic.get_kep_dan))

    c_text, c_table = st.columns([1, 1])
    with c_text:
        st.info("📝 Mẫu văn bản (Copy)")
        txt_out = f"==== TOP GAN {l2_src} ({shorten_date(dt_show[0]['date'])}) ====\n\n"
        for item in stats:
            if item:
                val_txt = logic.doc_so_chu(item['Giá trị']) if str(item['Giá trị']).isdigit() else str(item['Giá trị'])
                txt_out += f"{item['Loại']}: {val_txt}\nDàn: {item['Dàn']}\nLâu ra: {item['Chữ']} ngày\n---\n"
        txt_out += "#xoso #thongke\n⛔ Chỉ mang tính chất tham khảo!"
        st.text_area("Nội dung:", txt_out, height=500)

    with c_table:
        st.success("🏆 Bảng Gan Tổng Hợp")
        df_stats = pd.DataFrame([s for s in stats if s])
        if not df_stats.empty:
            st.dataframe(df_stats[["Loại", "Giá trị", "Số ngày", "Dàn"]], hide_index=True, use_container_width=True)
        
        st.markdown("#### ☠️ Top 10 Số Đề Gan")
        last_seen_num = {}
        for idx, val in enumerate(all_tails):
            if val not in last_seen_num: last_seen_num[val] = idx
        gan_nums = [{"Số": k, "Gan": v} for k,v in last_seen_num.items()]
        df_gan_nums = pd.DataFrame(gan_nums).sort_values("Gan", ascending=False).head(10)
        st.dataframe(df_gan_nums.T, use_container_width=True)

# --- TAB 5: DÒ CẦU ---
with tabs[4]:
    st.caption("Công Cụ Dò Cầu")
    target = st.text_input("Nhập cặp số (VD: 68):", max_chars=2)
    if target and len(target) == 2:
        found = []
        for x in full_xsmb[:days_fetch]:
            if target in x['number']: found.append({"Ngày": shorten_date(x['date']), "Nguồn": "GĐB", "Số": x['number']})
        for x in full_g1[:days_fetch]:
            if target in x['number']: found.append({"Ngày": shorten_date(x['date']), "Nguồn": "G1", "Số": x['number']})
        if found:
            st.success(f"Tìm thấy {len(found)} lần.")
            st.dataframe(pd.DataFrame(found), use_container_width=True, hide_index=True)
        else:
            st.warning("Không tìm thấy.")

# ------------------------------------------------------------------------------
# TAB 6: TẦN SUẤT (ĐIỆN TOÁN - KHUNG 7 NGÀY) - GIỐNG EXCEL
# ------------------------------------------------------------------------------
with tabs[5]:
    st.caption("Phân Tích Tần Suất Lô Tô (Khung 7 Ngày)")
    
    # 1. Xử lý dữ liệu theo logic Nhóm Tần Suất
    freq_rows = []
    
    # Cần ít nhất 7 ngày dữ liệu để tính
    if len(dt_show) < 7:
        st.warning("Cần ít nhất 7 ngày dữ liệu để tính tần suất.")
    else:
        # Duyệt từ ngày mới nhất -> cũ hơn
        # Dừng trước 7 ngày cuối cùng vì không đủ khung
        for i in range(len(dt_show) - 6):
            current_day = dt_show[i]
            date_str = shorten_date(current_day['date'])
            
            # Lấy KQ ngày hiện tại để hiển thị
            kq_str = "".join(current_day['numbers'])
            
            # Lấy cửa sổ 7 ngày (từ i đến i+7)
            # Vì list đang sort Mới -> Cũ, nên [i : i+7] là 7 ngày gần nhất tính từ ngày i
            window_7_days = dt_show[i : i+7]
            
            # Gộp tất cả số của 7 ngày lại thành 1 chuỗi khổng lồ
            merged_str = ""
            for day in window_7_days:
                merged_str += "".join(day['numbers'])
            
            # Đếm tần suất từng số 0-9
            counts_map = {str(d): merged_str.count(str(d)) for d in range(10)}
            
            # Đảo ngược map: {Tần suất: [Danh sách số]}
            # Ví dụ: {9 lần: ['1', '5'], 8 lần: ['3']}
            freq_groups = {}
            max_freq = 0 # Để xác định số cột cần vẽ
            
            for digit, count in counts_map.items():
                freq_groups.setdefault(count, []).append(digit)
                if count > max_freq: max_freq = count
            
            # Tạo dòng dữ liệu
            row = {
                "Ngày": date_str,
                "KQ": kq_str
            }
            
            # Điền vào các cột Tần suất (0, 1, 2...)
            # Giới hạn hiển thị đến cột 15 (thường 7 ngày khó vượt quá 15 lần)
            for f in range(16): 
                digits = freq_groups.get(f, [])
                # Sắp xếp và nối thành chuỗi "1,5"
                row[str(f)] = ",".join(sorted(digits))
            
            freq_rows.append(row)

        # --- HIỂN THỊ BẢNG ---
        df_freq = pd.DataFrame(freq_rows)
        
        # Cấu hình cột
        col_cfg = {
            "Ngày": st.column_config.TextColumn("Ngày", width="small"),
            "KQ": st.column_config.TextColumn("KQ/MỨC", width="medium"),
        }
        
        # Cấu hình các cột tần suất 0-15 cho nhỏ lại
        cols_to_style = []
        for f in range(16):
            col_name = str(f)
            # Chỉ hiện những cột có dữ liệu (để bảng đỡ rộng nếu max freq nhỏ)
            if col_name in df_freq.columns:
                 # Nếu cột toàn rỗng thì có thể ẩn, nhưng để giữ form giống excel ta cứ hiện
                col_cfg[col_name] = st.column_config.TextColumn(col_name, width="small")
                cols_to_style.append(col_name)

        # Tô màu:
        # - Cột 0, 1 (Ít ra/Gan): Màu xám
        # - Cột 2, 3, 4 (Trung bình): Màu trắng/đen
        # - Cột 5, 6, 7... (Ra nhiều - Hot): Màu đỏ giống Excel
        def highlight_cells(val):
            if not val: return ''
            return 'font-weight: bold' # Mặc định in đậm số

        def highlight_cols(row):
            styles = []
            for col in row.index:
                if col in ["Ngày", "KQ"]:
                    styles.append("")
                    continue
                
                try:
                    freq = int(col)
                    val = row[col]
                    if not val:
                        styles.append("")
                        continue
                        
                    if freq == 0:
                        styles.append('color: gray; font-style: italic;') # Gan (0 lần)
                    elif freq >= 8:
                        styles.append('color: #ff0000; font-weight: bold; background-color: #ffe6e6') # Rất Hot (Đỏ)
                    elif freq >= 5:
                        styles.append('color: #cc0000; font-weight: bold;') # Hot (Đỏ đậm)
                    else:
                        styles.append('color: black;') # Bình thường
                except:
                    styles.append("")
            return styles

        st.markdown("##### 🔢 Bảng Gom Nhóm Theo Tần Suất (7 Ngày)")
        st.dataframe(
            df_freq.style.apply(highlight_cols, axis=1),
            column_config=col_cfg,
            hide_index=True,
            use_container_width=False, # Co bảng lại cho gọn
            height=600
        )
        
        st.caption("**Giải thích:** Cột số (0, 1, 2...) là số lần xuất hiện. Nội dung trong ô là các chữ số tương ứng. VD: Cột 9 có số '1,5' nghĩa là trong 7 ngày qua, số 1 và số 5 đã về 9 lần.")

    st.divider()

    # --- PHẦN 2: HEATMAP 00-99 (GIỮ NGUYÊN VÌ HỮU ÍCH) ---
    st.markdown("##### 🗺️ Bản đồ nhiệt cặp số 00-99 (Toàn bộ)")
    # Tính lại toàn bộ để vẽ heatmap
    all_nums_str = "".join(["".join(x['numbers']) for x in dt_show])
    from collections import Counter
    # Đếm cặp 2 số bất kỳ (sliding window style nếu cần, ở đây đếm cặp 00-99 có mặt)
    pair_counts = {}
    for i in range(100):
        p = f"{i:02d}"
        pair_counts[p] = all_nums_str.count(p)
        
    grid = []
    for d in range(10):
        r = {"Đầu": str(d)}
        for u in range(10):
            r[str(u)] = pair_counts.get(f"{d}{u}", 0)
        grid.append(r)
    
    st.dataframe(
        pd.DataFrame(grid).set_index("Đầu").style.background_gradient(cmap="YlOrRd", axis=None),
        use_container_width=True
    )
