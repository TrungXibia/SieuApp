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
tabs = st.tabs(["📊 KẾT QUẢ", "🎯 DÀN NUÔI (MATRIX)", "🎲 BỆT CẦU", "🔍 TRA CỨU", "🧠 CÔNG CỤ THÔNG MINH"])

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
    src_mode = c1.selectbox("Nguồn:", ["Thần Tài", "Điện Toán"])
    comp_mode = c2.selectbox("So với:", ["XSMB (ĐB)", "Giải Nhất"])
    check_range = c3.slider("Khung nuôi (ngày):", 1, 20, 7)
    backtest_mode = c4.selectbox("Backtest:", ["Hiện tại", "Lùi 1 ngày", "Lùi 2 ngày", "Lùi 3 ngày", "Lùi 4 ngày", "Lùi 5 ngày"])
    
    if st.button("🚀 Phân Tích", type="primary"):
        backtest_offset = 0
        if backtest_mode != "Hiện tại":
            backtest_offset = int(backtest_mode.split()[1])
        
        if backtest_offset > 0:
            st.info(f"🔍 Backtest: Từ {backtest_offset} ngày trước")
        
        col_comp = "xsmb_2so" if comp_mode == "XSMB (ĐB)" else "g1_2so"
        
        all_days_data = []
        start_idx = backtest_offset
        end_idx = min(backtest_offset + 20, len(df_show))
        
        for i in range(start_idx, end_idx):
            row = df_full.iloc[i]
            src_str = ""
            if src_mode == "Thần Tài": 
                src_str = str(row.get('tt_number', ''))
            elif src_mode == "Điện Toán": 
                src_str = "".join(row.get('dt_numbers', []))
            
            if not src_str or src_str == "nan": 
                continue
            
            digits = set(src_str)
            combos = sorted({a+b for a in digits for b in digits})
            all_days_data.append({'date': row['date'], 'source': src_str, 'combos': combos, 'index': i})
        
        if not all_days_data:
            st.warning("⚠️ Không có dữ liệu")
        else:
            st.markdown("### 📋 Bảng Theo Dõi")
            table_html = "<table style='border-collapse: collapse; width: 100%; font-size: 13px;'><tr>"
            table_html += "<th style='padding: 8px; border: 1px solid #ddd; background-color: #f5f5f5; text-align: center; min-width: 80px;'>Ngày</th>"
            table_html += "<th style='padding: 8px; border: 1px solid #ddd; background-color: #f5f5f5; text-align: center; min-width: 60px;'>Giải</th>"
            table_html += "<th style='padding: 8px; border: 1px solid #ddd; background-color: #f5f5f5; text-align: center;'>Dàn nhị hợp</th>"
            table_html += "<th style='padding: 8px; border: 1px solid #ddd; background-color: #f5f5f5; text-align: center; min-width: 50px;'>Mức</th>"
            
            num_days = len(all_days_data)
            for k in range(1, num_days + 1):
                table_html += f"<th style='padding: 8px; border: 1px solid #ddd; background-color: #f5f5f5; text-align: center; min-width: 45px;'>N{k}</th>"
            table_html += "</tr>"
            
            for row_idx, day_data in enumerate(all_days_data):
                date, source, combos, i = day_data['date'], day_data['source'], day_data['combos'], day_data['index']
                dan_str = " ".join(combos[:15]) + ("..." if len(combos) > 15 else "")
                table_html += f"<tr><td style='padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold;'>{date}</td>"
                table_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{source}</td>"
                table_html += f"<td style='padding: 6px; border: 1px solid #ddd; font-size: 11px;'>{dan_str}</td>"
                table_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{len(combos)}</td>"
                
                num_cols_this_row = row_idx + 1
                for k in range(1, num_cols_this_row + 1):
                    idx = i - k
                    cell_val, bg_color, text_color = "", "white", "black"
                    if idx >= 0:
                        val_res = df_full.iloc[idx][col_comp]
                        if val_res in combos:
                            cell_val, bg_color, text_color = "✅", "#d4edda", "green"
                        else:
                            cell_val, bg_color, text_color = "--", "#fff3cd", "#856404"
                    table_html += f"<td style='padding: 8px; border: 1px solid #ddd; background-color: {bg_color}; color: {text_color}; font-weight: bold; text-align: center;'>{cell_val}</td>"
                
                for _ in range(num_days - row_idx - 1):
                    table_html += "<td style='border: 1px solid #eee; background-color: #f9f9f9;'></td>"
                table_html += "</tr>"
            
            table_html += "</table>"
            st.markdown(table_html, unsafe_allow_html=True)
            
            st.markdown("---")
            st.subheader("📊 Thống kê")
            total_days, total_checks, total_hits = len(all_days_data), 0, 0
            for row_idx, day_data in enumerate(all_days_data):
                combos, i = day_data['combos'], day_data['index']
                for k in range(1, row_idx + 2):
                    idx = i - k
                    if idx >= 0:
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
            st.caption("Các số chưa trúng trong tất cả các ngày, phân loại theo mức tần suất")
            
            all_pending_numbers = {}
            for row_idx, day_data in enumerate(all_days_data):
                combos = day_data['combos']
                i = day_data['index']
                num_cols_this_row = row_idx + 1
                hit_numbers = set()
                for k in range(1, num_cols_this_row + 1):
                    idx = i - k
                    if idx >= 0:
                        val_res = df_full.iloc[idx][col_comp]
                        if val_res in combos:
                            hit_numbers.add(val_res)
                pending = set(combos) - hit_numbers
                for num in pending:
                    all_pending_numbers[num] = all_pending_numbers.get(num, 0) + 1
            
            if all_pending_numbers:
                from collections import defaultdict
                level_groups = defaultdict(list)
                for num, count in all_pending_numbers.items():
                    level_groups[count].append(num)
                
                st.write("**Phân loại theo Mức (số lần xuất hiện trong các dàn):**")
                for freq in sorted(level_groups.keys(), reverse=True):
                    nums = sorted(level_groups[freq])
                    count = len(nums)
                    if freq >= 5:
                        bg_color, text_color, icon, label = "#ffebee", "#c62828", "🔥", "HOT"
                    elif freq >= 3:
                        bg_color, text_color, icon, label = "#fff3e0", "#e65100", "⚡", "Quan tâm"
                    else:
                        bg_color, text_color, icon, label = "#f5f5f5", "#616161", "📌", "Theo dõi"
                    
                    level_html = f"""<div style="background-color: {bg_color}; padding: 12px; margin: 8px 0; border-radius: 5px; border-left: 4px solid {text_color};"><div style="color: {text_color}; font-weight: bold; margin-bottom: 5px; font-size: 14px;">{icon} Mức {freq} ({count} số) - {label}</div><div style="color: {text_color}; font-size: 16px; font-weight: 500;">{', '.join(nums)}</div></div>"""
                    st.markdown(level_html, unsafe_allow_html=True)
                
                total_pending = len(all_pending_numbers)
                hot_pending = len([n for n, c in all_pending_numbers.items() if c >= 5])
                col_p1, col_p2, col_p3 = st.columns(3)
                col_p1.metric("Tổng số chưa ra", total_pending)
                col_p2.metric("Số HOT (≥5 lần)", hot_pending)
                col_p3.metric("Tỷ lệ HOT", f"{round(hot_pending/total_pending*100, 1)}%" if total_pending > 0 else "0%")
                st.caption("**Ghi chú:** 🔥 HOT (≥5 lần) → Ưu tiên nuôi | ⚡ Quan tâm (3-4 lần) | 📌 Theo dõi (1-2 lần)")
            else:
                st.success("✅ Tất cả các số đều đã trúng!")


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
        # Validation
        if not f_num.isdigit() or len(f_num) > 2:
            st.error("Vui lòng nhập số từ 0-99")
        else:
            f_num = f_num.zfill(2)
            mask = df_full.apply(lambda r: f_num in str(r['xsmb_full']) or f_num in str(r['g1_full']), axis=1)
            found = df_full[mask][['date', 'xsmb_full', 'g1_full']]
            if not found.empty:
                st.success(f"Tìm thấy {len(found)} kết quả.")
                st.dataframe(found, use_container_width=True)
            else:
                st.warning("Không tìm thấy.")

# === TAB 5: CÔNG CỤ THÔNG MINH ===
with tabs[4]:
    st.header("🧠 Công cụ Phân tích Thông minh")
    
    tool_tabs = st.tabs(["🔢 Tần suất", "🎯 Dự đoán", "⏱️ Chu kỳ", "📊 Thống kê", "🔍 Pattern"])
    
    # Tool 1: Phân tích tần suất
    with tool_tabs[0]:
        st.subheader("Phân tích Tần suất Xuất hiện")
        col1, col2 = st.columns(2)
        
        with col1:
            source_col = st.selectbox("Chọn nguồn:", ["XSMB (ĐB)", "Giải Nhất"], key="freq_source")
            top_n = st.slider("Số lượng hiển thị:", 5, 30, 15, key="freq_top")
        
        col_name = "xsmb_2so" if source_col == "XSMB (ĐB)" else "g1_2so"
        
        if st.button("📊 Phân tích", type="primary", key="freq_btn"):
            freq_data = logic.phan_tich_tan_suat(df_full, col_name, top_n)
            
            if freq_data:
                # Hiển thị bảng
                df_freq = pd.DataFrame([
                    {"Số": k, "Số lần": v, "Tỷ lệ %": round(v/len(df_full)*100, 1)}
                    for k, v in freq_data.items()
                ])
                
                col_a, col_b = st.columns([1, 1])
                with col_a:
                    st.dataframe(df_freq, use_container_width=True, hide_index=True)
                
                # Biểu đồ
                with col_b:
                    import plotly.graph_objects as go
                    fig = go.Figure(data=[
                        go.Bar(x=list(freq_data.keys()), y=list(freq_data.values()),
                               marker_color='lightblue', text=list(freq_data.values()),
                               textposition='auto')
                    ])
                    fig.update_layout(title="Biểu đồ Tần suất", xaxis_title="Số", 
                                     yaxis_title="Số lần", height=400)
                    st.plotly_chart(fig, use_container_width=True)
    
    # Tool 2: Dự đoán bộ số
    with tool_tabs[1]:
        st.subheader("Dự đoán Bộ số Thông minh")
        st.caption("Dựa trên phân tích tần suất và chu kỳ")
        
        pred_source = st.selectbox("Chọn nguồn:", ["XSMB (ĐB)", "Giải Nhất"], key="pred_source")
        pred_col = "xsmb_2so" if pred_source == "XSMB (ĐB)" else "g1_2so"
        
        if st.button("🎯 Dự đoán", type="primary", key="pred_btn"):
            predictions = logic.du_doan_bo_so(df_full, pred_col, 15)
            
            if predictions:
                df_pred = pd.DataFrame(predictions)
                df_pred.columns = ["Số", "Tần suất", "Chu kỳ TB", "Ngày chưa về", "Độ tin cậy %"]
                
                # Highlight theo độ tin cậy
                def color_confidence(val):
                    if isinstance(val, (int, float)):
                        if val >= 80: return 'background-color: #d4edda; font-weight: bold'
                        elif val >= 60: return 'background-color: #fff3cd'
                        else: return 'background-color: #f8d7da'
                    return ''
                
                st.dataframe(
                    df_pred.style.map(color_confidence, subset=['Độ tin cậy %']),
                    use_container_width=True, hide_index=True
                )
                
                st.info("💡 **Gợi ý:** Số có độ tin cậy cao và đã lâu chưa về có khả năng xuất hiện sớm.")
            else:
                st.warning("Không đủ dữ liệu để dự đoán.")
    
    # Tool 3: Phân tích chu kỳ
    with tool_tabs[2]:
        st.subheader("Phân tích Chu kỳ Xuất hiện")
        
        col1, col2 = st.columns(2)
        with col1:
            cycle_num = st.text_input("Nhập số cần phân tích (00-99):", max_chars=2, key="cycle_num")
        with col2:
            cycle_source = st.selectbox("Nguồn:", ["XSMB (ĐB)", "Giải Nhất"], key="cycle_source")
        
        if cycle_num and cycle_num.isdigit():
            cycle_col = "xsmb_2so" if cycle_source == "XSMB (ĐB)" else "g1_2so"
            cycle_info = logic.tim_chu_ky(df_full, cycle_num, cycle_col)
            
            if cycle_info["so_lan_xuat_hien"] > 0:
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Số lần xuất hiện", cycle_info["so_lan_xuat_hien"])
                
                if cycle_info["chu_ky_trung_binh"]:
                    col_b.metric("Chu kỳ trung bình", f"{cycle_info['chu_ky_trung_binh']} ngày")
                    col_c.metric("Ngày chưa về", f"{cycle_info['lan_gan_nhat']} ngày")
                    
                    # Biểu đồ khoảng cách
                    if cycle_info["khoang_cach"]:
                        import plotly.graph_objects as go
                        fig = go.Figure(data=[
                            go.Scatter(y=cycle_info["khoang_cach"], mode='lines+markers',
                                      line=dict(color='royalblue', width=2),
                                      marker=dict(size=8))
                        ])
                        fig.update_layout(title="Khoảng cách giữa các lần xuất hiện",
                                         xaxis_title="Lần", yaxis_title="Số ngày", height=300)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        avg = cycle_info["chu_ky_trung_binh"]
                        last = cycle_info["lan_gan_nhat"]
                        if last >= avg * 0.9:
                            st.success(f"🔥 Số {cycle_num.zfill(2)} đã {last} ngày chưa về, gần đến chu kỳ TB ({avg} ngày)!")
                        else:
                            st.info(f"Số {cycle_num.zfill(2)} mới về {last} ngày trước.")
                else:
                    st.warning("Chưa đủ dữ liệu để tính chu kỳ (cần ít nhất 2 lần xuất hiện).")
            else:
                st.warning(f"Số {cycle_num.zfill(2)} chưa xuất hiện trong dữ liệu.")
    
    # Tool 4: Thống kê nâng cao
    with tool_tabs[3]:
        st.subheader("Thống kê Nâng cao")
        
        stat_type = st.radio("Chọn loại thống kê:", 
                            ["Cặp số thường đi cùng", "Phân bố tổng quát"],
                            horizontal=True)
        
        if stat_type == "Cặp số thường đi cùng":
            if st.button("📊 Phân tích", key="pair_btn"):
                pairs = logic.thong_ke_cap_so(df_full, "xsmb_2so", "g1_2so")
                
                if pairs:
                    df_pairs = pd.DataFrame(pairs)
                    df_pairs.columns = ["Cặp số (ĐB - G1)", "Số lần cùng xuất hiện"]
                    st.dataframe(df_pairs, use_container_width=True, hide_index=True)
                    st.caption("*Các cặp số xuất hiện cùng ngày (ĐB và G1)*")
                else:
                    st.info("Không tìm thấy cặp số nào xuất hiện >= 2 lần.")
        
        else:  # Phân bố tổng quát
            import plotly.graph_objects as go
            import numpy as np
            
            # Lấy tất cả số từ ĐB
            all_nums = df_full['xsmb_2so'].dropna().astype(str).str.zfill(2).tolist()
            
            # Tạo heat map 10x10
            matrix = np.zeros((10, 10))
            for num in all_nums:
                if len(num) == 2:
                    row, col = int(num[0]), int(num[1])
                    matrix[row][col] += 1
            
            fig = go.Figure(data=go.Heatmap(
                z=matrix,
                x=list(range(10)),
                y=list(range(10)),
                colorscale='YlOrRd',
                text=matrix.astype(int),
                texttemplate="%{text}",
                textfont={"size": 10}
            ))
            fig.update_layout(title="Heat Map Tần suất (Hàng chục x Đơn vị)",
                            xaxis_title="Đơn vị", yaxis_title="Hàng chục",
                            height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    # Tool 5: Tìm Pattern
    with tool_tabs[4]:
        st.subheader("Tìm Pattern Lặp lại")
        st.caption("Phát hiện chuỗi số xuất hiện liên tiếp nhiều lần")
        
        pattern_source = st.selectbox("Nguồn:", ["XSMB (ĐB)", "Giải Nhất"], key="pattern_source")
        pattern_col = "xsmb_2so" if pattern_source == "XSMB (ĐB)" else "g1_2so"
        
        if st.button("🔍 Tìm Pattern", type="primary", key="pattern_btn"):
            patterns = logic.phan_tich_pattern(df_full, pattern_col, min_length=2)
            
            if patterns:
                df_patterns = pd.DataFrame(patterns)
                df_patterns.columns = ["Pattern", "Độ dài", "Số lần lặp", "Vị trí (5 đầu)"]
                
                # Highlight pattern xuất hiện nhiều
                def highlight_freq(val):
                    if isinstance(val, int):
                        if val >= 5: return 'background-color: #d4edda; font-weight: bold'
                        elif val >= 3: return 'background-color: #fff3cd'
                    return ''
                
                st.dataframe(
                    df_patterns.style.map(highlight_freq, subset=['Số lần lặp']),
                    use_container_width=True, hide_index=True
                )
                
                st.info("💡 **Gợi ý:** Pattern lặp lại nhiều lần có thể là dấu hiệu của chu kỳ đặc biệt.")
            else:
                st.warning("Không tìm thấy pattern nào lặp lại.")
