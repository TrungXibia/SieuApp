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

# ==========================================
# TAB 3: BỆT (KÈM CHECK 7 NGÀY)
# ==========================================
with tabs[2]:
    st.caption("Thống Kê Bệt & Kiểm Tra 7 Ngày")
    
    c_src, c_type = st.columns([1, 2])
    with c_src:
        b_src = st.selectbox("Nguồn:", ["GĐB", "G1", "Thần Tài"], label_visibility="collapsed")
    with c_type:
        b_types = st.multiselect("Kiểu:", ["Bệt Phải", "Thẳng", "Bệt trái"], default=["Bệt Phải", "Thẳng"])
    
    if b_src == "GĐB": s_dat = xsmb_show
    elif b_src == "G1": s_dat = g1_show
    else: s_dat = tt_show
    
    gdb_tails = [x['number'][-2:] for x in full_xsmb]
    
    bet_rows = []
    for i in range(len(s_dat)-1):
        curr, nxt = s_dat[i], s_dat[i+1]
        found = set()
        for t in b_types:
            found.update(logic.tim_chu_so_bet(list(curr['number']), list(nxt['number']), t))
        
        if not found: continue
        
        dancham = logic.lay_dan_cham(list(found))
        t1 = gdb_tails[i] if i < len(gdb_tails) else ""
        t2 = gdb_tails[i+1] if i+1 < len(gdb_tails) else ""
        nhihop = logic.lay_nhi_hop(list(found), list(t1)+list(t2))
        final_dan = sorted(set(dancham + nhihop))
        
        row = {
            "Ngày": shorten_date(curr['date']),
            "Bệt": ",".join(sorted(found)),
            "Dàn": " ".join(final_dan),
        }
        
        # Check T1 -> T7
        for k in range(1, 8):
            check_idx = i - k
            col_name = f"T{k}"
            if check_idx >= 0:
                res_val = gdb_tails[check_idx]
                if res_val in final_dan:
                    row[col_name] = res_val
                else:
                    row[col_name] = ""
            else:
                row[col_name] = "?"
        
        bet_rows.append(row)
            
    if bet_rows:
        df_bet = pd.DataFrame(bet_rows)
        
        def highlight_hits(val):
            if val and val != "?" and val.isdigit():
                return 'background-color: #ccffcc; color: black; font-weight: bold;'
            elif val == "?":
                return 'color: gray;'
            return ''

        col_cfg = {
            "Ngày": st.column_config.TextColumn("Ngày", width="small"),
            "Bệt": st.column_config.TextColumn("Bệt", width="small"),
            "Dàn": st.column_config.TextColumn("Dàn Nuôi", width="medium"),
        }
        for k in range(1, 8):
            col_cfg[f"T{k}"] = st.column_config.TextColumn(f"{k}", width="small")

        st.dataframe(
            df_bet.style.applymap(highlight_hits, subset=[f"T{k}" for k in range(1, 8)]),
            column_config=col_cfg,
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("Không có dữ liệu bệt.")

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

