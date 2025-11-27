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

# --- CSS FIX LỖI FONT & GIAO DIỆN + RESPONSIVE ---
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
    
    /* === RESPONSIVE TABLE WRAPPER === */
    .table-wrapper {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        margin: 10px 0;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* === RESPONSIVE TABLE STYLES === */
    .responsive-table {
        border-collapse: collapse;
        width: 100%;
        font-size: 12px;
        min-width: 600px; /* Minimum width để table không bị vỡ */
    }
    
    .responsive-table th {
        padding: 6px 4px;
        border: 1px solid #34495e;
        background-color: #2c3e50;
        color: white;
        text-align: center;
        white-space: nowrap;
        position: sticky;
        top: 0;
        z-index: 10;
        font-size: 11px;
    }
    
    .responsive-table td {
        padding: 5px 3px;
        border: 1px solid #dee2e6;
        text-align: center;
    }
    
    /* Sticky first 2 columns on desktop */
    @media (min-width: 768px) {
        .responsive-table th:nth-child(1),
        .responsive-table td:nth-child(1) {
            position: sticky;
            left: 0;
            z-index: 5;
            background-color: #2c3e50;
        }
        
        .responsive-table td:nth-child(1) {
            background-color: inherit;
            font-weight: bold;
        }
        
        .responsive-table th:nth-child(2),
        .responsive-table td:nth-child(2) {
            position: sticky;
            left: 80px;
            z-index: 5;
        }
    }
    
    /* === MOBILE RESPONSIVE (< 768px) === */
    @media (max-width: 767px) {
        .responsive-table {
            font-size: 11px;
            min-width: 100%;
        }
        
        .responsive-table th {
            padding: 4px 3px;
            font-size: 10px;
        }
        
        .responsive-table td {
            padding: 4px 2px;
            font-size: 11px;
        }
        
        /* Giảm width cho cột ngày và giải */
        .responsive-table th:nth-child(1),
        .responsive-table td:nth-child(1) {
            min-width: 70px;
            font-size: 10px;
        }
        
        .responsive-table th:nth-child(2),
        .responsive-table td:nth-child(2) {
            min-width: 50px;
        }
        
        .responsive-table th:nth-child(3),
        .responsive-table td:nth-child(3) {
            min-width: 120px;
            font-size: 9px;
        }
        
        .responsive-table th:nth-child(4),
        .responsive-table td:nth-child(4) {
            min-width: 40px;
        }
        
        /* Cột N1, N2, N3... */
        .responsive-table th:nth-child(n+5),
        .responsive-table td:nth-child(n+5) {
            min-width: 32px;
            padding: 3px 2px;
        }
    }
    
    /* === EXTRA SMALL MOBILE (< 480px) === */
    @media (max-width: 479px) {
        .responsive-table {
            font-size: 10px;
        }
        
        .responsive-table th {
            padding: 3px 2px;
            font-size: 9px;
        }
        
        .responsive-table td {
            padding: 3px 1px;
            font-size: 10px;
        }
        
        .responsive-table th:nth-child(1),
        .responsive-table td:nth-child(1) {
            min-width: 60px;
            font-size: 9px;
        }
        
        .responsive-table th:nth-child(2),
        .responsive-table td:nth-child(2) {
            min-width: 45px;
        }
        
        .responsive-table th:nth-child(3),
        .responsive-table td:nth-child(3) {
            min-width: 100px;
            font-size: 8px;
        }
        
        .responsive-table th:nth-child(n+5),
        .responsive-table td:nth-child(n+5) {
            min-width: 30px;
            padding: 2px 1px;
        }
    }
    
    /* Scroll indicator hint */
    .scroll-hint {
        text-align: center;
        color: #7f8c8d;
        font-size: 12px;
        margin-top: 5px;
        display: none;
    }
    
    @media (max-width: 767px) {
        .scroll-hint {
            display: block;
        }
    }
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
tabs = st.tabs(["📊 KẾT QUẢ", "🎯 DÀN NUÔI (MATRIX)", "🎲 BỆT CẦU", "📊 THỐNG KÊ", "🔎 DÒ CẦU", "📈 TẦN SUẤT"])

# --- DATA PREPARATION FOR NEW TABS ---
def shorten_date(d):
    # Loại bỏ phần thứ nếu có (ví dụ: "Thứ Tư ngày 26-11-2025" -> "26/11")
    if "ngày" in d:
        d = d.split("ngày")[-1].strip()  # Lấy phần sau "ngày"
    # Chuyển từ dd-mm-yyyy hoặc dd/mm/yyyy sang dd/mm
    d = d.replace("-", "/")
    return "/".join(d.split("/")[:2])

dt_show = []
for _, row in df_show.iterrows():
    dt_show.append({
        'date': row['date'],
        'numbers': row['dt_numbers'] if isinstance(row['dt_numbers'], list) else []
    })

full_xsmb = []
full_g1 = []
for _, row in df_full.iterrows():
    full_xsmb.append({'date': row['date'], 'number': str(row['xsmb_full'])})
    full_g1.append({'date': row['date'], 'number': str(row['g1_full'])})


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

# === TAB 2: DÀN NUÔI (SIMPLE VIEW) ===
with tabs[1]:
    c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1.5])
    src_mode = c1.selectbox("Nguồn:", ["Thần Tài", "Điện Toán", "Cả 2 (ĐT + TT)"])
    comp_mode = c2.selectbox("So với:", ["XSMB (ĐB)", "Giải Nhất"])
    check_range = c3.slider("Khung nuôi (ngày):", 1, 20, 7)
    backtest_mode = c4.selectbox("Backtest:", ["Hiện tại", "Lùi 1 ngày", "Lùi 2 ngày", "Lùi 3 ngày", "Lùi 4 ngày", "Lùi 5 ngày"])
    
    # Tự động phân tích
    backtest_offset = 0
    if backtest_mode != "Hiện tại":
        backtest_offset = int(backtest_mode.split()[1])
    
    if backtest_offset > 0:
        st.info(f"🔍 Backtest: Từ {backtest_offset} ngày trước")
    
    col_comp = "xsmb_2so" if comp_mode == "XSMB (ĐB)" else "g1_2so"
    
    all_days_data = []
    start_idx = backtest_offset
    end_idx = min(backtest_offset + 20, len(df_full))  # Sử dụng df_full thay vì df_show
    
    for i in range(start_idx, end_idx):
        row = df_full.iloc[i]
        src_str = ""
        if src_mode == "Thần Tài": 
            src_str = str(row.get('tt_number', ''))
        elif src_mode == "Điện Toán": 
            src_str = "".join(row.get('dt_numbers', []))
        elif src_mode == "Cả 2 (ĐT + TT)":
            dt_val = "".join(row.get('dt_numbers', []))
            tt_val = str(row.get('tt_number', ''))
            if tt_val == 'nan': tt_val = ""
            src_str = dt_val + tt_val
        
        if not src_str or src_str == "nan": 
            continue
        
        digits = set(src_str)
        combos = sorted({a+b for a in digits for b in digits})
        all_days_data.append({'date': row['date'], 'source': src_str, 'combos': combos, 'index': i})
    
    if not all_days_data:
        st.warning("⚠️ Không có dữ liệu")
    else:
        st.markdown("### 📋 Bảng Theo Dõi")
        
        # Wrapper div cho responsive
        table_html = "<div class='table-wrapper'>"
        table_html += "<table class='responsive-table'><tr>"
        table_html += "<th>Ngày</th>"
        table_html += "<th>Giải</th>"
        table_html += "<th>Dàn nhị hợp</th>"
        table_html += "<th>Mức</th>"
        
        num_days = len(all_days_data)
        for k in range(1, num_days + 1):
            table_html += f"<th>N{k}</th>"
        table_html += "</tr>"
        
        for row_idx, day_data in enumerate(all_days_data):
            date, source, combos, i = day_data['date'], day_data['source'], day_data['combos'], day_data['index']
            dan_str = " ".join(combos[:15]) + ("..." if len(combos) > 15 else "")
            row_bg = "#f8f9fa" if row_idx % 2 == 0 else "#ffffff"
            table_html += f"<tr style='background-color: {row_bg};'><td style='font-weight: bold; color: #2c3e50;'>{date}</td>"
            table_html += f"<td style='color: #495057;'>{source}</td>"
            table_html += f"<td style='font-size: 11px; color: #495057;'>{dan_str}</td>"
            table_html += f"<td style='font-weight: 600; color: #2c3e50;'>{len(combos)}</td>"
            
            num_cols_this_row = row_idx + 1
            for k in range(1, num_cols_this_row + 1):
                idx = i - k
                cell_val, bg_color, text_color = "", "#ecf0f1", "#7f8c8d"
                
                # Chỉ hiển thị kết quả nếu idx >= backtest_offset (không xem "tương lai")
                if idx >= 0 and idx >= backtest_offset:
                    val_res = df_full.iloc[idx][col_comp]
                    if val_res in combos:
                        cell_val, bg_color, text_color = "✅", "#27ae60", "white"
                    else:
                        cell_val, bg_color, text_color = "--", "#e74c3c", "white"
                table_html += f"<td style='background-color: {bg_color}; color: {text_color}; font-weight: bold;'>{cell_val}</td>"
            
            for _ in range(num_days - row_idx - 1):
                table_html += "<td style='background-color: #ecf0f1;'></td>"
            table_html += "</tr>"
        
        table_html += "</table></div>"
        table_html += "<div class='scroll-hint'>👆 Vuốt ngang để xem thêm →</div>"
        st.markdown(table_html, unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("📊 Thống kê")
        total_days, total_checks, total_hits = len(all_days_data), 0, 0
        for row_idx, day_data in enumerate(all_days_data):
            combos, i = day_data['combos'], day_data['index']
            for k in range(1, row_idx + 2):
                idx = i - k
                # Chỉ tính nếu idx >= backtest_offset (không tính "tương lai")
                if idx >= 0 and idx >= backtest_offset:
                    total_checks += 1
                    if df_full.iloc[idx][col_comp] in combos:
                        total_hits += 1
        
        hit_rate = round(total_hits / total_checks * 100, 1) if total_checks > 0 else 0
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("Tổng ngày", total_days)
        col_s2.metric("Tổng kiểm tra", total_checks)
        col_s3.metric("Đã trúng", total_hits)
        col_s4.metric("Tỷ lệ", f"{hit_rate}%")
        
        # === TỔNG HỢP DÀN CHƯA RA ===
        st.markdown("---")
        st.subheader("🎯 Tổng hợp Dàn Chưa Ra")
        st.caption("Các dàn nhị hợp chưa ra (chưa trúng số nào)")
        
        # Thu thập dữ liệu theo ngày - chỉ những dàn HOÀN TOÀN chưa ra
        from datetime import datetime
        pending_by_date = []
        
        for row_idx, day_data in enumerate(all_days_data):
            combos = day_data['combos']
            date = day_data['date']
            i = day_data['index']
            num_cols_this_row = row_idx + 1
            hit_numbers = set()
            
            # Kiểm tra xem có số nào trong dàn đã trúng chưa (chỉ xét dữ liệu lịch sử)
            for k in range(1, num_cols_this_row + 1):
                idx = i - k
                if idx >= 0 and idx >= backtest_offset:
                    val_res = df_full.iloc[idx][col_comp]
                    if val_res in combos:
                        hit_numbers.add(val_res)
            
            # Nếu CHƯA có số nào trúng (hit_numbers rỗng) thì dàn này chưa ra
            if not hit_numbers:
                # Parse date để lấy thứ
                try:
                    date_obj = datetime.strptime(date, "%d/%m/%Y")
                    weekday_names = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
                    weekday = weekday_names[date_obj.weekday()]
                except:
                    weekday = ""
                
                pending_by_date.append({
                    'Ngày': f"{weekday} {date}" if weekday else date,
                    'Dàn nhị hợp': ', '.join(sorted(combos)),
                    'Số lượng': len(combos),
                    'combos': combos  # Giữ lại để phân tích tần suất
                })
        
        if pending_by_date:
            # Hiển thị bảng theo ngày
            df_display = pd.DataFrame([{k: v for k, v in item.items() if k != 'combos'} for item in pending_by_date])
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Phân tích tần suất các số trong các dàn chưa ra
            st.markdown("---")
            st.markdown("**📊 Mức số trong các dàn chưa ra:**")
            st.caption("Đếm số lần xuất hiện của mỗi số trong tất cả các dàn chưa ra")
            
            # Đếm tần suất
            from collections import defaultdict
            number_frequency = defaultdict(int)
            for item in pending_by_date:
                for num in item['combos']:
                    number_frequency[num] += 1
            
            # Nhóm theo mức (bao gồm mức 0)
            level_groups = defaultdict(list)
            for num, freq in number_frequency.items():
                level_groups[freq].append(num)
            
            # Tìm tất cả số từ 00-99 và thêm mức 0
            all_possible_numbers = {f"{i:02d}" for i in range(100)}
            numbers_in_pending = set(number_frequency.keys())
            level_0_numbers = sorted(all_possible_numbers - numbers_in_pending)
            
            if level_0_numbers:
                level_groups[0] = level_0_numbers
            
            # Hiển thị theo mức giảm dần
            for freq in sorted(level_groups.keys(), reverse=True):
                nums = sorted(level_groups[freq])
                st.write(f"**Mức {freq}** ({len(nums)} số): {', '.join(nums)}")
            
            # Thống kê tổng quan
            st.markdown("---")
            total_days_pending = len(pending_by_date)
            total_unique_numbers = len(number_frequency)
            col_p1, col_p2 = st.columns(2)
            col_p1.metric("Số ngày có dàn chưa ra", total_days_pending)
            col_p2.metric("Tổng số unique trong các dàn", total_unique_numbers)
        else:
            st.success("✅ Tất cả các dàn đều đã ra (có ít nhất 1 số trúng)!")
        
        # === PHÂN TÍCH CHU KỲ & NHẬN ĐỊNH ===
        st.markdown("---")
        st.subheader("🔮 Phân tích Chu kỳ & Nhận định")
        st.caption("Dựa trên dữ liệu bảng theo dõi")
        
        # Thu thập dữ liệu chu kỳ cho mỗi dàn
        cycle_analysis = []
        
        for row_idx, day_data in enumerate(all_days_data):
            combos = day_data['combos']
            date = day_data['date']
            i = day_data['index']
            
            # Phân tích dữ liệu từ bảng theo dõi
            num_cols_this_row = row_idx + 1
            hits = []  # Vị trí các lần trúng (1, 2, 3...)
            misses = []  # Vị trí các lần không trúng
            
            for k in range(1, num_cols_this_row + 1):
                idx = i - k
                if idx >= 0 and idx >= backtest_offset:
                    val_res = df_full.iloc[idx][col_comp]
                    if val_res in combos:
                        hits.append(k)
                    else:
                        misses.append(k)
            
            # Tính toán chu kỳ và nhận định
            total_checks = len(hits) + len(misses)
            hit_count = len(hits)
            miss_count = len(misses)
            
            if total_checks == 0:
                status = "🆕 Mới tạo - Chưa có dữ liệu"
                avg_cycle_display = "N/A"
                last_hit_display = "N/A"
                priority = 2
                overdue = 0
            elif hit_count == 0:
                # Chưa ra lần nào
                status = f"🔥 Chưa ra ({total_checks} ngày kiểm tra) - Ưu tiên cao"
                avg_cycle_display = "Chưa ra"
                last_hit_display = "Chưa bao giờ"
                priority = 0
                overdue = total_checks
            else:
                # Đã ra ít nhất 1 lần
                # Tính chu kỳ giữa các lần trúng
                if len(hits) > 1:
                    cycles = [hits[j-1] - hits[j] for j in range(1, len(hits))]
                    avg_cycle = round(sum(cycles) / len(cycles), 1)
                else:
                    avg_cycle = hits[0]
                
                avg_cycle_display = f"{avg_cycle} ngày"
                last_hit_display = f"N{hits[0]}"
                
                # Nhận định dựa trên chu kỳ
                days_since_last = hits[0] - 1  # Số ngày từ lần trúng cuối
                
                if days_since_last == 0:
                    status = "✅ Vừa trúng hôm qua"
                    priority = 2
                    overdue = 0
                elif days_since_last < avg_cycle:
                    remaining = round(avg_cycle - days_since_last)
                    status = f"⏳ Trong chu kỳ (còn ~{remaining} ngày)"
                    priority = 2
                    overdue = 0
                else:
                    overdue_days = days_since_last - avg_cycle
                    if overdue_days > avg_cycle * 0.5:
                        status = f"⚠️ Quá chu kỳ {round(overdue_days)} ngày - Ưu tiên cao"
                        priority = 1
                        overdue = overdue_days
                    else:
                        status = f"📍 Quá chu kỳ {round(overdue_days)} ngày"
                        priority = 1
                        overdue = overdue_days
            
            cycle_analysis.append({
                'Ngày': date,
                'Dàn': ', '.join(sorted(combos)),
                'Chu kỳ TB': avg_cycle_display,
                'Lần cuối ra': last_hit_display,
                'Đã kiểm tra': total_checks,
                'Trúng/Trượt': f"{hit_count}/{miss_count}",
                'Nhận định': status,
                # Thêm các trường ẩn để sắp xếp
                '_sort_priority': priority,
                '_overdue_days': overdue,
                '_total_checks': total_checks
            })
        
        if cycle_analysis:
            # Sắp xếp: Ưu tiên chưa ra (nhiều ngày nhất), sau đó quá chu kỳ nhiều nhất, sau đó trong chu kỳ
            cycle_analysis.sort(key=lambda x: (x['_sort_priority'], -x['_overdue_days'], -x['_total_checks']))
            
            # Loại bỏ các trường ẩn trước khi hiển thị
            cycle_analysis_display = [{k: v for k, v in item.items() if not k.startswith('_')} for item in cycle_analysis]
            
            df_cycle = pd.DataFrame(cycle_analysis_display)
            st.dataframe(df_cycle, use_container_width=True, hide_index=True)
            
            # Gợi ý ưu tiên
            st.markdown("---")
            st.markdown("**💡 Gợi ý ưu tiên theo dõi:**")
            
            # Lọc các dàn ưu tiên cao
            priority_sets = [item for item in cycle_analysis if "Ưu tiên cao" in item['Nhận định'] or "Chưa ra lần nào" in item['Nhận định']]
            
            if priority_sets:
                st.info(f"Có **{len(priority_sets)}** dàn cần ưu tiên theo dõi (quá hạn hoặc chưa ra lần nào)")
                
                # Hiển thị danh sách dàn ưu tiên
                st.markdown("**📋 Danh sách dàn ưu tiên:**")
                for idx, item in enumerate(priority_sets, 1):
                    st.write(f"{idx}. **{item['Ngày']}**: {item['Dàn']} - _{item['Nhận định']}_")
                
                # Phân tích mức số trong các dàn ưu tiên
                st.markdown("---")
                st.markdown("**📊 Mức số trong các dàn ưu tiên:**")
                
                from collections import defaultdict
                priority_number_freq = defaultdict(int)
                
                # Đếm tần suất từ dàn gốc (không phải string đã format)
                for row_idx, day_data in enumerate(all_days_data):
                    date = day_data['date']
                    combos = day_data['combos']
                    
                    # Kiểm tra xem dàn này có trong danh sách ưu tiên không
                    is_priority = any(p['Ngày'] == date for p in priority_sets)
                    
                    if is_priority:
                        for num in combos:
                            priority_number_freq[num] += 1
                
                # Nhóm theo mức (bao gồm mức 0)
                level_groups_priority = defaultdict(list)
                for num, freq in priority_number_freq.items():
                    level_groups_priority[freq].append(num)
                
                # Tìm tất cả số từ 00-99 và thêm mức 0
                all_possible_numbers = {f"{i:02d}" for i in range(100)}
                numbers_in_priority = set(priority_number_freq.keys())
                level_0_numbers = sorted(all_possible_numbers - numbers_in_priority)
                
                if level_0_numbers:
                    level_groups_priority[0] = level_0_numbers
                
                # Hiển thị theo mức giảm dần
                for freq in sorted(level_groups_priority.keys(), reverse=True):
                    nums = sorted(level_groups_priority[freq])
                    st.write(f"**Mức {freq}** ({len(nums)} số): {', '.join(nums)}")
            else:
                st.success("Tất cả các dàn đang trong chu kỳ bình thường")
        else:
            pass  # Không có dữ liệu để phân tích chu kỳ


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
                 "Ngày": shorten_date(df_show.iloc[i]['date']),
                 "Hôm nay": curr,
                 "Hôm qua": prev,
                 "Số Bệt": ",".join(bet_nums)
             })
    
    if bet_data:
        st.dataframe(pd.DataFrame(bet_data), use_container_width=True)
    else:
        st.info("Không tìm thấy cầu bệt trong phạm vi hiển thị.")

# ------------------------------------------------------------------------------
# TAB 4: THỐNG KÊ
# ------------------------------------------------------------------------------
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
    
    # === MỨC SỐ CỦA CÁC DÀN GAN ===
    st.divider()
    st.markdown("### 📊 Mức Số của các Dàn Gan")
    st.caption("Phân tích tần suất xuất hiện của các số trong tất cả các dàn gan")
    
    # Thu thập tất cả các số từ các dàn gan
    from collections import defaultdict
    number_frequency = defaultdict(int)
    
    # Duyệt qua tất cả các dàn gan và đếm tần suất
    for item in stats:
        if item and item['Dàn']:
            # Parse dàn (có thể là dạng "12,34,56" hoặc "12 34 56")
            dan_str = str(item['Dàn'])
            # Tách các số (dùng cả dấu phấy và khoảng trắng)
            numbers = dan_str.replace(',', ' ').split()
            for num in numbers:
                num = num.strip()
                if num and len(num) == 2 and num.isdigit():
                    number_frequency[num] += 1
    
    # Nhóm theo mức (bao gồm mức 0)
    level_groups = defaultdict(list)
    for num, freq in number_frequency.items():
        level_groups[freq].append(num)
    
    # Tìm tất cả số từ 00-99 và thêm mức 0
    all_possible_numbers = {f"{i:02d}" for i in range(100)}
    numbers_in_gan = set(number_frequency.keys())
    level_0_numbers = sorted(all_possible_numbers - numbers_in_gan)
    
    if level_0_numbers:
        level_groups[0] = level_0_numbers
    
    # Hiển thị theo mức giảm dần
    col_muc1, col_muc2 = st.columns([1, 3])
    
    with col_muc1:
        st.info("📈 Thống kê tổng quan")
        st.metric("Tổng số dàn gan", len([s for s in stats if s]))
        st.metric("Số unique trong dàn", len(number_frequency))
        st.metric("Số hoàn toàn không có", len(level_0_numbers))
        max_level = max(level_groups.keys()) if level_groups else 0
        st.metric("Mức cao nhất", max_level)
    
    with col_muc2:
        st.success("🎯 Bảng Mức Số")
        
        # Tạo bảng hiển thị đẹp hơn
        muc_data = []
        for freq in sorted(level_groups.keys(), reverse=True):
            nums = sorted(level_groups[freq])
            nums_display = ', '.join(nums)
            muc_data.append({
                "Mức": freq,
                "Số lượng": len(nums),
                "Các số": nums_display
            })
        
        df_muc = pd.DataFrame(muc_data)
        st.dataframe(
            df_muc,
            column_config={
                "Mức": st.column_config.NumberColumn("Mức", width="small"),
                "Số lượng": st.column_config.NumberColumn("Số lượng", width="small"),
                "Các số": st.column_config.TextColumn("Các số", width="large")
            },
            hide_index=True,
            use_container_width=True,
            height=400
        )
    
    # Phân tích chi tiết
    st.divider()
    st.markdown("#### 🔍 Chi tiết theo mức")
    
    # Tạo tabs cho các mức khác nhau
    levels = sorted(level_groups.keys(), reverse=True)
    if len(levels) > 0:
        # Chỉ hiển thị các mức có ý nghĩa (không hiển thị mức 0 nếu quá nhiều)
        significant_levels = [l for l in levels if l > 0]
        if 0 in levels and len(level_groups[0]) <= 50:
            significant_levels.append(0)
        
        # Hiển thị từng mức
        for freq in significant_levels[:10]:  # Giới hạn 10 mức để tránh quá dài
            nums = sorted(level_groups[freq])
            
            # Định dạng màu sắc dựa trên mức
            if freq == 0:
                color_emoji = "⚪"
                description = "Không xuất hiện trong bất kỳ dàn gan nào"
            elif freq >= 5:
                color_emoji = "🔴"
                description = "Xuất hiện rất nhiều - Ưu tiên cao"
            elif freq >= 3:
                color_emoji = "🟠"
                description = "Xuất hiện nhiều - Cần chú ý"
            elif freq >= 2:
                color_emoji = "🟡"
                description = "Xuất hiện trung bình"
            else:
                color_emoji = "🟢"
                description = "Xuất hiện ít"
            
            with st.expander(f"{color_emoji} **Mức {freq}** ({len(nums)} số) - {description}", expanded=(freq > 0 and freq >= 3)):
                st.write(f"**Danh sách:** {', '.join(nums)}")

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
# TAB 6: TẦN SUẤT (ĐIỆN TOÁN - KHUNG 7 NGÀY)
# ------------------------------------------------------------------------------
with tabs[5]:
    st.caption("Phân Tích Tần Suất Lô Tô (Khung 7 Ngày)")
    
    # Thêm lựa chọn nguồn dữ liệu
    freq_source = st.radio("Nguồn dữ liệu:", ["Cả 2 (ĐT + TT)", "Chỉ Điện Toán", "Chỉ Thần Tài"], horizontal=True, key="freq_source")
    
    if len(dt_show) < 7:
        st.warning("Cần ít nhất 7 ngày dữ liệu để tính tần suất.")
    else:
        # 1. TẦN SUẤT 0-9 (TOP 3)
        st.markdown("##### 1. Tần suất chữ số 0-9")
        freq_rows_digits = []
        
        for i in range(len(dt_show) - 6):
            current_day = dt_show[i]
            date_str = shorten_date(current_day['date'])
            kq_dt = "".join(current_day['numbers'])
            
            # Lấy kết quả ĐB và TT từ df_show
            xsmb_db = df_show.iloc[i].get('xsmb_full', '')
            tt_num = str(df_show.iloc[i].get('tt_number', ''))
            
            # Tạo cột hiển thị dựa trên lựa chọn
            if freq_source == "Cả 2 (ĐT + TT)":
                display_val = kq_dt + tt_num if tt_num and tt_num != 'nan' else kq_dt
            elif freq_source == "Chỉ Điện Toán":
                display_val = kq_dt
            else:  # Chỉ Thần Tài
                display_val = tt_num if tt_num and tt_num != 'nan' else ""
            
            # Nối dữ liệu trong khung 7 ngày dựa trên lựa chọn
            window_7_days = dt_show[i : i+7]
            merged_str = ""
            for idx, day in enumerate(window_7_days):
                if freq_source in ["Cả 2 (ĐT + TT)", "Chỉ Điện Toán"]:
                    merged_str += "".join(day['numbers'])  # Điện Toán
                if freq_source in ["Cả 2 (ĐT + TT)", "Chỉ Thần Tài"]:
                    tt_val = str(df_show.iloc[i + idx].get('tt_number', ''))
                    if tt_val and tt_val != 'nan':
                        merged_str += tt_val  # Thần Tài
            
            counts_map = {str(d): merged_str.count(str(d)) for d in range(10)}
            
            freq_groups = {}
            for digit, count in counts_map.items():
                freq_groups.setdefault(count, []).append(digit)
            
            row = {"STT": i + 1, "Ngày": date_str, "KQ": display_val, "KQ (ĐB)": str(xsmb_db)}
            sorted_freqs = sorted(freq_groups.keys(), reverse=True)
            top_3 = sorted_freqs[:3]
            disp_grps = []
            for f in top_3:
                disp_grps.append("".join(sorted(freq_groups[f])))
            row["TOP 3"] = " ".join(disp_grps)
            
            for f in range(16): 
                row[str(f)] = ",".join(sorted(freq_groups.get(f, [])))
            freq_rows_digits.append(row)

        df_digits = pd.DataFrame(freq_rows_digits)
        # Lọc bỏ các cột tần suất rỗng
        freq_cols = [str(f) for f in range(16) if str(f) in df_digits.columns]
        non_empty_freq_cols = [col for col in freq_cols if df_digits[col].str.strip().any()]
        cols = ["STT", "Ngày", "KQ", "KQ (ĐB)"] + non_empty_freq_cols + ["TOP 3"]
        df_digits = df_digits[cols]

        col_cfg_digits = {
            "STT": st.column_config.NumberColumn("STT", width=30, help="Số thứ tự"),
            "Ngày": st.column_config.TextColumn("Ngày", width=50),
            "KQ": st.column_config.TextColumn("KQ", width=120, help="Kết quả theo nguồn đã chọn"),
            "KQ (ĐB)": st.column_config.TextColumn("KQ (ĐB)", width=100, help="Kết quả Đặc Biệt"),
            "TOP 3": st.column_config.TextColumn("TOP 3 (0-9)", width=100),
        }
        for f in range(16):
            if str(f) in df_digits.columns:
                col_cfg_digits[str(f)] = st.column_config.TextColumn(str(f), width=60)

        def highlight_cols_digits(row):
            styles = []
            for col in row.index:
                val = row[col]
                if col == "TOP 3":
                    styles.append('background-color: #ffffcc; color: #d63031; font-weight: bold; border-left: 2px solid #ccc;')
                    continue
                if col in ["STT", "Ngày", "KQ", "KQ (ĐB)"]: styles.append(""); continue
                try:
                    freq = int(col)
                    if not val: styles.append("")
                    elif freq == 0: styles.append('color: #808080; font-style: italic;')
                    elif freq >= 8: styles.append('background-color: #ff4b4b; color: #ffffff; font-weight: bold;')
                    elif freq >= 5: styles.append('background-color: #ffcccc; color: #000000; font-weight: bold;')
                    else: styles.append('')
                except: styles.append("")
            return styles

        st.dataframe(df_digits.style.apply(highlight_cols_digits, axis=1), column_config=col_cfg_digits, hide_index=True, use_container_width=True)

        st.divider()

        # 2. TẦN SUẤT 00-99 (TOP 2)
        st.markdown("##### 2. Tần suất cặp số 00-99")
        
        freq_rows_pairs = []
        for i in range(len(dt_show) - 6):
            current_day = dt_show[i]
            date_str = shorten_date(current_day['date'])
            kq_dt = "".join(current_day['numbers'])
            
            # Lấy kết quả ĐB và TT từ df_show
            xsmb_db = df_show.iloc[i].get('xsmb_full', '')
            tt_num = str(df_show.iloc[i].get('tt_number', ''))
            
            # Tạo cột hiển thị dựa trên lựa chọn
            if freq_source == "Cả 2 (ĐT + TT)":
                display_val = kq_dt + tt_num if tt_num and tt_num != 'nan' else kq_dt
            elif freq_source == "Chỉ Điện Toán":
                display_val = kq_dt
            else:  # Chỉ Thần Tài
                display_val = tt_num if tt_num and tt_num != 'nan' else ""
            
            # Nối dữ liệu trong khung 7 ngày dựa trên lựa chọn
            window_7_days = dt_show[i : i+7]
            merged_str = ""
            for idx, day in enumerate(window_7_days):
                if freq_source in ["Cả 2 (ĐT + TT)", "Chỉ Điện Toán"]:
                    merged_str += "".join(day['numbers'])  # Điện Toán
                if freq_source in ["Cả 2 (ĐT + TT)", "Chỉ Thần Tài"]:
                    tt_val = str(df_show.iloc[i + idx].get('tt_number', ''))
                    if tt_val and tt_val != 'nan':
                        merged_str += tt_val  # Thần Tài
            
            counts_map = {}
            for num in range(100):
                pair = f"{num:02d}"
                counts_map[pair] = merged_str.count(pair)
            
            freq_groups = {}
            max_freq = 0
            for pair, count in counts_map.items():
                freq_groups.setdefault(count, []).append(pair)
                if count > max_freq: max_freq = count
            
            row = {"STT": i + 1, "Ngày": date_str, "KQ": display_val, "KQ (ĐB)": str(xsmb_db)}
            sorted_freqs = sorted(freq_groups.keys(), reverse=True)
            top_2 = sorted_freqs[:2]
            disp_grps = []
            for f in top_2:
                disp_grps.append(",".join(sorted(freq_groups[f])))
            row["TOP 2"] = " | ".join(disp_grps)
            
            limit_col = max(8, max_freq + 1)
            for f in range(limit_col): 
                pairs = freq_groups.get(f, [])
                row[str(f)] = " ".join(sorted(pairs))
            freq_rows_pairs.append(row)

        df_pairs = pd.DataFrame(freq_rows_pairs)
        # Lọc bỏ các cột tần suất rỗng
        freq_cols_p = [str(f) for f in range(limit_col) if str(f) in df_pairs.columns]
        non_empty_freq_cols_p = [col for col in freq_cols_p if df_pairs[col].str.strip().any()]
        cols_p = ["STT", "Ngày", "KQ", "KQ (ĐB)"] + non_empty_freq_cols_p + ["TOP 2"]
        df_pairs = df_pairs[cols_p]

        col_cfg_pairs = {
            "STT": st.column_config.NumberColumn("STT", width=50, help="Số thứ tự"),
            "Ngày": st.column_config.TextColumn("Ngày", width=80),
            "KQ": st.column_config.TextColumn("KQ", width=150, help="Kết quả theo nguồn đã chọn"),
            "KQ (ĐB)": st.column_config.TextColumn("KQ (ĐB)", width=80, help="Kết quả Đặc Biệt"),
            "TOP 2": st.column_config.TextColumn("TOP 2 (Cao nhất)", width=200),
        }
        for f in range(limit_col):
            if str(f) in df_pairs.columns:
                col_cfg_pairs[str(f)] = st.column_config.TextColumn(str(f), width=80)

        def highlight_cols_pairs(row):
            styles = []
            for col in row.index:
                val = row[col]
                if col == "TOP 2":
                    styles.append('background-color: #e6f7ff; color: #0050b3; font-weight: bold; border-left: 2px solid #ccc;')
                    continue
                if col in ["STT", "Ngày", "KQ", "KQ (ĐB)"]: styles.append(""); continue
                try:
                    freq = int(col)
                    if not val: styles.append("")
                    elif freq == 0: styles.append('color: #808080; font-style: italic;')
                    elif freq >= 4: styles.append('background-color: #ff4b4b; color: #ffffff; font-weight: bold;')
                    elif freq >= 2: styles.append('background-color: #ffcccc; color: #000000; font-weight: bold;')
                    else: styles.append('')
                except: styles.append("")
            return styles

        st.dataframe(df_pairs.style.apply(highlight_cols_pairs, axis=1), column_config=col_cfg_pairs, hide_index=True, use_container_width=True)


