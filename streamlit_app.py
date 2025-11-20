import streamlit as st
import pandas as pd
import logic
import data_fetcher
from collections import Counter

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(
    page_title="SIÊU GÀ APP",
    page_icon="🐔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS TÙY CHỈNH ---
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] { 
        height: 45px; 
        white-space: pre-wrap; 
        background-color: #f0f2f6; 
        border-radius: 4px 4px 0 0; 
        gap: 1px; 
        padding-top: 8px; 
        padding-bottom: 8px;
        font-size: 14px;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #ffffff; 
        border-top: 2px solid #ff4b4b; 
    }
    /* Chỉnh bảng trên mobile cho gọn */
    div[data-testid="stDataFrame"] div[class^="stDataFrame"] td {
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# --- HÀM TIỆN ÍCH ---
def shorten_date(date_str):
    """Rút gọn ngày: 'Thứ Tư ngày 19-11-2025' -> '19/11'"""
    try:
        parts = date_str.split(" ")
        raw_date = parts[-1] 
        day_mon = raw_date[:5] 
        return day_mon
    except:
        return date_str

# --- QUẢN LÝ DỮ LIỆU (CACHE) ---
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
    days_show = st.slider("Hiển thị (ngày)", 10, 60, 30)
    
    if st.button("🔄 Cập nhật dữ liệu"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Phiên bản v3.0 (Full Features)")

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

# --- MAIN TABS ---
tabs = st.tabs(["📊 Kết Quả", "🎯 Dàn Nuôi", "🎲 Bệt (Bet)", "📈 Thống Kê 2 Số", "🔍 Dò Cầu"])

# ==========================================
# TAB 1: KẾT QUẢ
# ==========================================
with tabs[0]:
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Điện Toán 123")
        if dt_show:
            df_dt = pd.DataFrame(dt_show)
            # Tạo bản sao để hiển thị ngày rút gọn
            df_dt_disp = df_dt.copy()
            df_dt_disp['date'] = df_dt_disp['date'].apply(shorten_date)
            df_dt_disp['Chuỗi số'] = df_dt_disp['numbers'].apply(lambda x: " - ".join(x))
            
            st.dataframe(
                df_dt_disp[['date', 'Chuỗi số']], 
                hide_index=True, 
                use_container_width=True,
                column_config={
                    "date": st.column_config.TextColumn("Ngày", width="small"),
                    "Chuỗi số": "Kết Quả"
                }
            )
    with c2:
        st.caption("Thần Tài")
        if tt_show:
            df_tt_disp = pd.DataFrame(tt_show).copy()
            df_tt_disp['date'] = df_tt_disp['date'].apply(shorten_date)
            st.dataframe(df_tt_disp, hide_index=True, use_container_width=True, 
                         column_config={"date": st.column_config.TextColumn("Ngày", width="small"), "number":"Số"})
    
    st.divider()
    c3, c4 = st.columns(2)
    with c3:
        st.caption("XSMB (GĐB)")
        if xsmb_show:
            df_xsmb_disp = pd.DataFrame(xsmb_show).copy()
            df_xsmb_disp['date'] = df_xsmb_disp['date'].apply(shorten_date)
            st.dataframe(df_xsmb_disp, hide_index=True, use_container_width=True,
                         column_config={"date": st.column_config.TextColumn("Ngày", width="small"), "number":"Số"})
    with c4:
        st.caption("Giải Nhất (G1)")
        if g1_show:
            df_g1_disp = pd.DataFrame(g1_show).copy()
            df_g1_disp['date'] = df_g1_disp['date'].apply(shorten_date)
            st.dataframe(df_g1_disp, hide_index=True, use_container_width=True,
                         column_config={"date": st.column_config.TextColumn("Ngày", width="small"), "number":"Số"})

# ==========================================
# TAB 2: DÀN NUÔI (KÈM MỨC SỐ + CỘT BÉ)
# ==========================================
with tabs[1]:
    st.caption("Phân Tích & Thống Kê Mức Số")
    
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
                if check_idx >= 0:
                    val_ref = ref_data[check_idx]["number"][-2:]
                
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
            
            if hits == 0 and i <= 30: 
                missed_str = " ".join(sorted(combos))
                missed_patterns.append(f"📅 {shorten_date(dt_show[i]['date'])} ({val}): {missed_str}")
                raw_missed_data.append(missed_str)

        df_res = pd.DataFrame(results)
        
        def color_status(val):
            return f'background-color: {"#ffcccc" if val == "MISS" else "#ccffcc"}'

        if not df_res.empty:
            # Cấu hình cột hiển thị
            col_config = {
                "Ngày": st.column_config.TextColumn("Ngày", width="small"),
                "KQ": st.column_config.TextColumn("KQ", width="small"), 
                "Dàn": st.column_config.TextColumn("Dàn Nuôi", width="medium"),
                "TT": st.column_config.TextColumn("TT", width="small"),
            }
            
            # Cấu hình cột K1->K21: Đổi tên thành 1->21 và ép size nhỏ
            for k_col in [c for c in df_res.columns if c.startswith("K")]:
                col_config[k_col] = st.column_config.TextColumn(
                    k_col.replace("K", ""), 
                    width="small"
                )

            st.dataframe(
                df_res.style.applymap(color_status, subset=['TT']),
                column_config=col_config,
                use_container_width=True,
                hide_index=True
            )
        
        # Thống kê mức số
        if missed_patterns:
            st.divider()
            c_warn, c_stat = st.columns([1, 1])
            with c_warn:
                st.warning("⚠️ CÁC DÀN CHƯA NỔ (30 ngày gần nhất)")
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
                        disp = []
                        for n in nums:
                            if n == latest_ref_val:
                                disp.append(f"<span style='color:red; font-weight:bold; border:1px solid red; padding:2px'>{n}</span>")
                            else:
                                disp.append(n)
                        st.markdown(f"**Mức {lvl}** ({len(nums)} số): {', '.join(disp)}", unsafe_allow_html=True)
                    st.caption(f"*Số đỏ: Trùng với KQ mới nhất ({latest_ref_val})*")

# === TAB 3: BỆT (GIAO DIỆN PC STYLE) ===
with tabs[2]:
    # CSS riêng cho Tab này để giống phần mềm PC (font nhỏ, cột hẹp)
    st.markdown("""
    <style>
        div[data-testid="stDataFrame"] td { font-size: 12px; padding: 2px !important; }
        div[data-testid="stDataFrame"] th { font-size: 12px; padding: 2px !important; }
    </style>
    """, unsafe_allow_html=True)

    # --- 1. KHUNG CẤU HÌNH TRÊN CÙNG ---
    with st.container():
        c_cfg1, c_cfg2 = st.columns([1, 3])
        with c_cfg1:
            # Chọn nguồn cho bảng chi tiết bên trái
            target_src = st.selectbox("Nguồn phân tích (Bảng trái):", ["GĐB", "G1", "Thần Tài"], index=0)
        with c_cfg2:
            # Chọn kiểu bệt áp dụng chung
            st.write("Kiểu bệt:")
            c_b1, c_b2, c_b3 = st.columns(3)
            use_phai = c_b1.checkbox("Bệt Phải (Cheo)", value=True)
            use_thang = c_b2.checkbox("Thẳng", value=True)
            use_trai = c_b3.checkbox("Bệt Trái", value=True)
            
            bet_types = []
            if use_phai: bet_types.append("Bệt Phải")
            if use_thang: bet_types.append("Thẳng")
            if use_trai: bet_types.append("Bệt trái")

    st.divider()

    # --- 2. XỬ LÝ DỮ LIỆU ---
    # Lấy dữ liệu tham chiếu (GĐB 2 số cuối) để check kết quả
    gdb_tails = [x['number'][-2:] for x in full_xsmb]
    
    # Hàm tạo dataframe chi tiết (Bên trái)
    def create_detail_df(source_name, b_types):
        if source_name == "GĐB": src_data = xsmb_show
        elif source_name == "G1": src_data = g1_show
        else: src_data = tt_show
        
        rows = []
        for i in range(len(src_data)-1):
            curr = src_data[i]
            nxt = src_data[i+1]
            
            # 1. Tách số (A B C D E)
            nums = list(curr['number'])
            if len(nums) < 5: nums = ['']*(5-len(nums)) + nums
            else: nums = nums[-5:]
            
            # 2. Tìm Bệt
            found = set()
            for t in b_types:
                found.update(logic.tim_chu_so_bet(list(curr['number']), list(nxt['number']), t))
            
            # 3. Tạo dàn
            dancham = []
            nhihop = []
            final_dan = []
            
            if found:
                dancham = logic.lay_dan_cham(list(found))
                t1 = gdb_tails[i] if i < len(gdb_tails) else ""
                t2 = gdb_tails[i+1] if i+1 < len(gdb_tails) else ""
                nhihop = logic.lay_nhi_hop(list(found), list(t1)+list(t2))
                final_dan = sorted(set(dancham + nhihop))

            # 4. Check kết quả (F1 -> F15)
            check_cols = {}
            has_win_row = False
            
            for k in range(1, 16):
                chk_idx = i - k
                val_chk = "0" # Mặc định trượt
                
                if chk_idx >= 0:
                    res = gdb_tails[chk_idx]
                    if final_dan and res in final_dan:
                        val_chk = "1" # Trúng
                        has_win_row = True
                else:
                    val_chk = "" # Chưa có KQ
                
                check_cols[f"F{k}"] = val_chk

            # 5. Đóng gói dòng
            row_item = {
                "date": shorten_date(curr['date']),
                "A": nums[0], "B": nums[1], "C": nums[2], "D": nums[3], "E": nums[4],
                "N1": curr['number'][-2:], # 2 số cuối
                "Chạm": "".join(sorted(found)),
                "Bet": ",".join(sorted(found)),
                "Dàn": " ".join(final_dan) if final_dan else "",
                "WIN": has_win_row # Cờ tô màu
            }
            row_item.update(check_cols)
            rows.append(row_item)
            
        return pd.DataFrame(rows)

    # Hàm tạo dataframe tổng hợp (Bên phải)
    def create_summary_df(b_types):
        srcs = [("ĐB", xsmb_show), ("G1", g1_show), ("TT", tt_show)]
        summary_rows = []
        for i in range(len(xsmb_show)-1):
            row_item = {"date": shorten_date(xsmb_show[i]['date'])}
            for name, data in srcs:
                curr = data[i]
                nxt = data[i+1]
                found = set()
                for t in b_types:
                    found.update(logic.tim_chu_so_bet(list(curr['number']), list(nxt['number']), t))
                row_item[name] = ",".join(sorted(found))
            summary_rows.append(row_item)
        return pd.DataFrame(summary_rows)

    # --- 3. HIỂN THỊ GIAO DIỆN ---
    col_left, col_right = st.columns([65, 35]) 

    # === CỘT TRÁI ===
    with col_left:
        st.caption(f"📋 Chi tiết & Soi KQ nuôi ({target_src})")
        df_detail = create_detail_df(target_src, bet_types)
        
        if not df_detail.empty:
            # Tô màu dòng trúng
            def highlight_win_rows(row):
                color = 'color: red; font-weight: bold;' if row['WIN'] else ''
                return [color] * len(row)

            # Cấu hình cột
            cfg_left = {
                "date": st.column_config.TextColumn("Ngày", width="small"),
                "A": st.column_config.TextColumn("A", width="small"),
                "B": st.column_config.TextColumn("B", width="small"),
                "C": st.column_config.TextColumn("C", width="small"),
                "D": st.column_config.TextColumn("D", width="small"),
                "E": st.column_config.TextColumn("E", width="small"),
                "N1": st.column_config.TextColumn("N1", width="small"),
                "Chạm": st.column_config.TextColumn("Chạm", width="small"),
                "Bet": st.column_config.TextColumn("Bet", width="small"),
                "Dàn": st.column_config.TextColumn("Dàn Nuôi", width="large"),
                # SỬA LỖI Ở ĐÂY: Dùng TextColumn thay vì Column
                "WIN": st.column_config.TextColumn("W", hidden=True), 
            }
            for k in range(1, 16):
                cfg_left[f"F{k}"] = st.column_config.TextColumn(f"{k}", width="small")

            st.dataframe(
                df_detail.style.apply(highlight_win_rows, axis=1),
                column_config=cfg_left,
                hide_index=True,
                use_container_width=True,
                height=600
            )

    # === CỘT PHẢI ===
    with col_right:
        st.caption("📑 Tổng hợp (3 Đài)")
        df_summary = create_summary_df(bet_types)
        
        if not df_summary.empty:
            cfg_right = {
                "date": st.column_config.TextColumn("Ngày", width="small"),
                "ĐB": st.column_config.TextColumn("ĐB", width="small"),
                "G1": st.column_config.TextColumn("G1", width="small"),
                "TT": st.column_config.TextColumn("TT", width="small"),
            }
            st.dataframe(
                df_summary,
                column_config=cfg_right,
                hide_index=True,
                use_container_width=True,
                height=600
            )

# === TAB 4: THỐNG KÊ TOP GAN & COPY ===
with tabs[3]:
    st.caption("Thống Kê Top Lâu Ra & Tạo Mẫu Copy")
    
    # 1. Chọn nguồn
    l2_src = st.radio("Nguồn dữ liệu:", ["GĐB", "G1"], horizontal=True, key="l2_src_radio")
    dat_l2 = full_xsmb if l2_src == "GĐB" else full_g1
    all_tails = [x['number'][-2:] for x in dat_l2] # Lấy toàn bộ lịch sử để tính gan chính xác
    
    # --- HÀM TÍNH TOP GAN ---
    def find_top_gan(data_list, extract_func, label_name, get_dan_func):
        """Tìm phần tử gan lớn nhất trong danh mục"""
        last_seen = {}
        # Duyệt từ mới nhất về quá khứ để tìm lần xuất hiện gần nhất
        for idx, val in enumerate(data_list):
            k = extract_func(val)
            if k not in last_seen:
                last_seen[k] = idx # idx chính là số ngày gan
        
        if not last_seen: return None

        # Tìm cái nào gan lớn nhất
        top_val = max(last_seen, key=last_seen.get)
        days = last_seen[top_val]
        
        return {
            "Loại": label_name,
            "Giá trị": top_val,
            "Số ngày": days,
            "Chữ": logic.doc_so_chu(days),
            "Dàn": get_dan_func(top_val)
        }

    # --- TÍNH TOÁN ---
    stats = []
    
    # 1. Bộ
    stats.append(find_top_gan(all_tails, logic.bo, "Bộ", logic.get_bo_dan))
    # 2. Hiệu
    stats.append(find_top_gan(all_tails, logic.hieu, "Hiệu", logic.get_hieu_dan))
    # 3. Con Giáp
    stats.append(find_top_gan(all_tails, logic.zodiac, "Con Giáp", logic.get_zodiac_dan))
    # 4. Tổng
    stats.append(find_top_gan(all_tails, lambda x: str((int(x[0])+int(x[1]))%10), "Tổng", logic.get_tong_dan))
    # 5. Kép
    stats.append(find_top_gan(all_tails, logic.kep, "Kép", logic.get_kep_dan))

    # --- HIỂN THỊ ---
    c_text, c_table = st.columns([1, 1])
    
    # CỘT TRÁI: VĂN BẢN COPY
    with c_text:
        st.info("📝 Mẫu văn bản (Copy)")
        
        text_output = "📊 Dữ liệu thống kê tham khảo xổ số – KHÔNG phải chốt số hay cá cược!\n\n"
        if l2_src == "GĐB":
            text_output += f"==== TOP LÂU RA NHẤT ĐẶC BIỆT ({shorten_date(dt_show[0]['date'])}) ====\n\n"
        else:
            text_output += f"==== TOP LÂU RA NHẤT GIẢI NHẤT ({shorten_date(dt_show[0]['date'])}) ====\n\n"
        
        for item in stats:
            if item:
                # Xử lý đọc tên giá trị (VD: Bộ 44 -> bộ bốn bốn)
                val_read = str(item['Giá trị'])
                if val_read.isdigit():
                    val_read_text = logic.doc_so_chu(val_read)
                else:
                    val_read_text = val_read # Giữ nguyên chữ (VD: K.LECH, Mão)

                text_output += f"{item['Loại']}: {val_read_text}\n"
                text_output += f"Dàn: {item['Dàn']}\n"
                text_output += f"Lâu ra: {item['Chữ']} ngày\n"
                text_output += "-----------------------------\n\n"
        
        text_output += "#thongke #xoso #thongkexoso #statistical #lottery #thongkedeso\n\n"
        text_output += "⛔ Không khuyến khích cá cược, không bán số, chỉ là thống kê!"
        
        st.text_area("Nội dung:", text_output, height=450)

    # CỘT PHẢI: BẢNG TEST TỔNG HỢP
    with c_table:
        st.success("🏆 Bảng Test Tổng Hợp (Top Gan)")
        
        # Chuyển đổi list stats thành DataFrame
        df_stats = pd.DataFrame([s for s in stats if s])
        if not df_stats.empty:
            # Sắp xếp lại cột
            df_disp = df_stats[["Loại", "Giá trị", "Số ngày", "Dàn"]]
            
            st.dataframe(
                df_disp,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Loại": st.column_config.TextColumn("Danh Mục", width="small"),
                    "Giá trị": st.column_config.TextColumn("Top Gan", width="small"),
                    "Số ngày": st.column_config.NumberColumn("Gan (Ngày)", format="%d"),
                    "Dàn": st.column_config.TextColumn("Dàn Số", width="medium"),
                }
            )
            
            st.markdown("---")
            st.caption("**Giải thích bảng:**")
            st.caption("- **Top Gan**: Giá trị (Bộ, Tổng...) lâu chưa về nhất tính đến hiện tại.")
            st.caption("- **Gan (Ngày)**: Số ngày liên tiếp chưa xuất hiện.")
            
            # Thống kê thêm: 10 số đề gan nhất (để tham khảo thêm)
            st.markdown("---")
            st.markdown("#### ☠️ Top 10 Số Đề Gan Nhất")
            
            last_seen_num = {}
            for idx, val in enumerate(all_tails):
                if val not in last_seen_num: last_seen_num[val] = idx
            
            gan_nums = [{"Số": k, "Gan": v} for k,v in last_seen_num.items()]
            df_gan_nums = pd.DataFrame(gan_nums).sort_values("Gan", ascending=False).head(10)
            
            st.dataframe(
                df_gan_nums.T, # Chuyển ngang cho dễ nhìn trên mobile
                use_container_width=True
            )

# ==========================================
# TAB 5: DÒ CẦU
# ==========================================
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



