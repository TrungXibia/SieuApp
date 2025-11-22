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

# === TAB 2: DÀN NUÔI (MATRIX VIEW) ===
with tabs[1]:
    c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1.5])
    src_mode = c1.selectbox("Nguồn:", ["Thần Tài", "Điện Toán"])
    comp_mode = c2.selectbox("So với:", ["XSMB (ĐB)", "Giải Nhất"])
    check_range = c3.slider("Khung nuôi (ngày):", 1, 20, 7)
    backtest_mode = c4.selectbox("Backtest:", [
        "Hiện tại",
        "Lùi 1 ngày",
        "Lùi 2 ngày",
        "Lùi 3 ngày",
        "Lùi 4 ngày",
        "Lùi 5 ngày"
    ])
    
    if st.button("🚀 Phân Tích Bảng Chéo", type="primary"):
        res_list = []
        pending_combos_all = []  # Lưu tất cả dàn chưa nổ
        col_comp = "xsmb_2so" if comp_mode == "XSMB (ĐB)" else "g1_2so"
        
        # Tính offset từ backtest mode
        backtest_offset = 0
        if backtest_mode != "Hiện tại":
            backtest_offset = int(backtest_mode.split()[1])
        
        # Hiển thị thông báo backtest
        if backtest_offset > 0:
            st.info(f"🔍 Đang backtest: Phân tích dàn từ {backtest_offset} ngày trước và kiểm tra kết quả trong {backtest_offset} ngày tiếp theo (đã biết)")
        
        # Điều chỉnh range với offset
        start_idx = backtest_offset
        end_idx = len(df_show)
        
        for i in range(start_idx, end_idx):
            row = df_full.iloc[i]
            # Lấy nguồn số
            src_str = ""
            if src_mode == "Thần Tài": src_str = str(row.get('tt_number', ''))
            elif src_mode == "Điện Toán": src_str = "".join(row.get('dt_numbers', []))
            
            if not src_str or src_str == "nan": continue
            
            # Tạo dàn
            digits = set(src_str)
            combos = {a+b for a in digits for b in digits}
            
            # Check các ngày tương lai (Quá khứ so với index hiện tại)
            k_cols = {}
            hits = 0
            first_hit = ""
            hit_combos = set()  # Các số đã trúng
            
            # Khi backtest, giới hạn check range trong khoảng đã biết
            max_check = min(check_range, i - backtest_offset) if backtest_offset > 0 else check_range
            
            for k in range(1, max_check + 1):
                idx = i - k
                val_res = ""
                cell_val = "" # Giá trị hiển thị trong ô
                
                if idx >= 0:
                    val_res = df_full.iloc[idx][col_comp]
                    if val_res in combos:
                        hits += 1
                        hit_combos.add(val_res)
                        cell_val = f"✅ {val_res}"
                        if not first_hit: first_hit = f"N{k}"
                
                k_cols[f"{k}"] = cell_val # Cột 1, 2, 3...
            
            # Tính dàn chưa nổ
            pending = sorted(combos - hit_combos)
            pending_count = len(pending)
            
            # Phân loại mức số
            total = len(combos)
            if total <= 10:
                level = "Mức 10"
            elif total <= 16:
                level = "Mức 16"
            elif total <= 25:
                level = "Mức 25"
            elif total <= 36:
                level = "Mức 36"
            else:
                level = f"Mức {total}"
            
            r = {
                "Ngày": row['date'],
                "Nguồn": src_str,
                "Mức": level,
                "Tổng": total,
                "Đã nổ": hits,
                "Chưa nổ": pending_count,
                "KQ": f"Ăn {first_hit}" if hits else "⏳",
                "Dàn chưa nổ": ", ".join(pending) if pending else "Đã hết"
            }
            r.update(k_cols)
            res_list.append(r)
            
            # Lưu dàn chưa nổ để hiển thị riêng
            if pending and hits == 0:  # Chỉ lấy dàn hoàn toàn chưa nổ
                pending_combos_all.append({
                    "Ngày": row['date'],
                    "Nguồn": src_str,
                    "Mức": level,
                    "Số lượng": pending_count,
                    "Dàn": ", ".join(pending)
                })
            
        if res_list:
            df_res = pd.DataFrame(res_list)
            
            # Hiển thị thống kê tổng quan
            st.subheader("📊 Tổng quan")
            col_a, col_b, col_c, col_d = st.columns(4)
            total_dans = len(df_res)
            dans_hit = len(df_res[df_res['KQ'].str.contains('Ăn', na=False)])
            dans_pending = total_dans - dans_hit
            hit_rate = round(dans_hit / total_dans * 100, 1) if total_dans > 0 else 0
            
            col_a.metric("Tổng dàn", total_dans)
            col_b.metric("Đã nổ", dans_hit)
            col_c.metric("Chưa nổ", dans_pending)
            col_d.metric("Tỷ lệ nổ", f"{hit_rate}%")
            
            st.markdown("---")
            
            # Bảng chính
            st.subheader("📋 Bảng phân tích chi tiết")
            
            # Config cột động
            col_cfg = {
                "Ngày": st.column_config.TextColumn("Ngày", width="small"),
                "Nguồn": st.column_config.TextColumn("Nguồn", width="small"),
                "Mức": st.column_config.TextColumn("Mức", width="small"),
                "Tổng": st.column_config.NumberColumn("Tổng", width="small"),
                "Đã nổ": st.column_config.NumberColumn("Đã nổ", width="small"),
                "Chưa nổ": st.column_config.NumberColumn("Chưa nổ", width="small"),
                "KQ": st.column_config.TextColumn("Trạng thái", width="small"),
                "Dàn chưa nổ": st.column_config.TextColumn("Dàn chưa nổ", width="large"),
            }
            # Các cột ngày K thu nhỏ lại
            cols_k = [str(k) for k in range(1, check_range + 1)]
            for k in cols_k:
                col_cfg[k] = st.column_config.TextColumn(f"N{k}", width="small")
            
            # Style màu sắc
            def highlight_cells(val):
                if "✅" in str(val):
                    return 'background-color: #d4edda; color: green; font-weight: bold; text-align: center'
                return ''
            
            def highlight_status(val):
                return 'background-color: #c3e6cb; color: darkgreen' if "Ăn" in str(val) else 'background-color: #f8d7da; color: maroon'
            
            def highlight_pending(val):
                if isinstance(val, (int, float)):
                    if val == 0:
                        return 'background-color: #d4edda; color: green; font-weight: bold'
                    elif val > 20:
                        return 'background-color: #f8d7da; color: maroon'
                    elif val > 10:
                        return 'background-color: #fff3cd; color: orange'
                return ''

            st.dataframe(
                df_res.style.map(highlight_cells, subset=cols_k)
                            .map(highlight_status, subset=['KQ'])
                            .map(highlight_pending, subset=['Chưa nổ']),
                column_config=col_cfg,
                hide_index=True, use_container_width=True
            )
            st.caption(f"*Chú thích: N1, N2... là ngày thứ 1, thứ 2 sau khi có cầu. Ô tích xanh là trúng.*")
            
            # === KẾT QUẢ BACKTEST ===
            if backtest_offset > 0:
                st.markdown("---")
                st.subheader("📊 KẾT QUẢ BACKTEST")
                st.caption(f"Kiểm tra độ chính xác của dự đoán từ {backtest_offset} ngày trước")
                
                # Tính toán metrics
                total_dans_bt = len(df_res)
                dans_hit_bt = len(df_res[df_res['KQ'].str.contains('Ăn', na=False)])
                dans_pending_bt = total_dans_bt - dans_hit_bt
                hit_rate_bt = round(dans_hit_bt / total_dans_bt * 100, 1) if total_dans_bt > 0 else 0
                
                # Hiển thị metrics
                col_bt1, col_bt2, col_bt3, col_bt4 = st.columns(4)
                col_bt1.metric("Ngày backtest", f"Lùi {backtest_offset} ngày")
                col_bt2.metric("Tổng dàn test", total_dans_bt)
                col_bt3.metric("Dàn đã trúng", dans_hit_bt, delta=f"{hit_rate_bt}%")
                col_bt4.metric("Dàn chưa trúng", dans_pending_bt)
                
                # Biểu đồ kết quả
                col_chart_bt1, col_chart_bt2 = st.columns(2)
                
                with col_chart_bt1:
                    import plotly.graph_objects as go
                    fig_bt = go.Figure(data=[
                        go.Bar(name='Đã trúng', x=['Backtest'], y=[dans_hit_bt], marker_color='lightgreen', text=[dans_hit_bt], textposition='auto'),
                        go.Bar(name='Chưa trúng', x=['Backtest'], y=[dans_pending_bt], marker_color='lightcoral', text=[dans_pending_bt], textposition='auto')
                    ])
                    fig_bt.update_layout(
                        title="Kết quả Backtest",
                        barmode='stack',
                        height=300,
                        showlegend=True
                    )
                    st.plotly_chart(fig_bt, use_container_width=True)
                
                with col_chart_bt2:
                    # Pie chart tỷ lệ
                    fig_pie = go.Figure(data=[
                        go.Pie(
                            labels=['Đã trúng', 'Chưa trúng'],
                            values=[dans_hit_bt, dans_pending_bt],
                            marker=dict(colors=['lightgreen', 'lightcoral']),
                            textinfo='label+percent',
                            hole=0.3
                        )
                    ])
                    fig_pie.update_layout(
                        title=f"Tỷ lệ trúng: {hit_rate_bt}%",
                        height=300
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                # Đánh giá
                if hit_rate_bt >= 70:
                    st.success(f"✅ Tuyệt vời! Tỷ lệ trúng {hit_rate_bt}% - Dự đoán rất chính xác!")
                elif hit_rate_bt >= 50:
                    st.info(f"ℹ️ Khá tốt! Tỷ lệ trúng {hit_rate_bt}% - Dự đoán ở mức trung bình khá")
                elif hit_rate_bt >= 30:
                    st.warning(f"⚠️ Tỷ lệ trúng {hit_rate_bt}% - Cần cải thiện chiến lược")
                else:
                    st.error(f"❌ Tỷ lệ trúng {hit_rate_bt}% - Nên xem xét lại phương pháp")
            
            # Hiển thị danh sách dàn chưa nổ
            if pending_combos_all:
                st.markdown("---")
                st.subheader("🎯 Danh sách Dàn Chưa Nổ (100%)")
                st.caption("Các dàn hoàn toàn chưa trúng trong khung nuôi")
                
                df_pending = pd.DataFrame(pending_combos_all)
                
                # Phân loại theo mức
                st.write("**Phân loại theo mức số:**")
                level_groups = df_pending.groupby('Mức').size().reset_index(name='Số lượng dàn')
                
                col_x, col_y = st.columns([1, 2])
                with col_x:
                    st.dataframe(level_groups, hide_index=True, use_container_width=True)
                
                with col_y:
                    import plotly.graph_objects as go
                    fig = go.Figure(data=[
                        go.Bar(x=level_groups['Mức'], y=level_groups['Số lượng dàn'],
                               marker_color='lightcoral', text=level_groups['Số lượng dàn'],
                               textposition='auto')
                    ])
                    fig.update_layout(title="Phân bố Dàn chưa nổ theo Mức", 
                                     xaxis_title="Mức", yaxis_title="Số lượng",
                                     height=300)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Bảng chi tiết
                st.write("**Chi tiết các dàn:**")
                st.dataframe(df_pending, hide_index=True, use_container_width=True)
                
                # Export option
                csv = df_pending.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Tải xuống danh sách (CSV)",
                    data=csv,
                    file_name=f"dan_chua_no_{src_mode}_{comp_mode}.csv",
                    mime="text/csv"
                )
                
                # === PHẦN MỚI: NHỊ HỢP THEO NGÀY ===
                st.markdown("---")
                st.subheader("🔢 Nhị Hợp Chưa Nổ Theo Ngày")
                st.caption("Danh sách nhị hợp chưa nổ của từng ngày (bao gồm kép)")
                
                # Tạo nhị hợp cho từng ngày
                nhi_hop_by_date = []
                all_nhi_hop_freq = {}  # Để đếm tần suất tổng
                
                for item in pending_combos_all:
                    date = item['Ngày']
                    dan_str = item['Dàn']
                    numbers = [n.strip() for n in dan_str.split(',')]
                    
                    # Lấy tất cả chữ số unique
                    digits = set()
                    for num in numbers:
                        for digit in num:
                            digits.add(digit)
                    
                    # Tạo nhị hợp (bao gồm kép)
                    nhi_hop_set = set()
                    for d1 in sorted(digits):
                        for d2 in sorted(digits):
                            nhi_hop_set.add(d1 + d2)
                    
                    nhi_hop_list = sorted(nhi_hop_set)
                    
                    # Đếm tần suất trong lịch sử cho từng số
                    nhi_hop_with_freq = []
                    for num in nhi_hop_list:
                        count = 0
                        for val in df_full[col_comp].dropna():
                            if str(val).zfill(2)[-2:] == num:
                                count += 1
                        nhi_hop_with_freq.append((num, count))
                        
                        # Cập nhật tần suất tổng
                        if num not in all_nhi_hop_freq:
                            all_nhi_hop_freq[num] = count
                    
                    nhi_hop_by_date.append({
                        'date': date,
                        'source': item['Nguồn'],
                        'nhi_hop': nhi_hop_with_freq,
                        'total': len(nhi_hop_list)
                    })
                
                
                # Hiển thị theo từng ngày với badge màu
                for idx, item in enumerate(nhi_hop_by_date):
                    # Tạo badge ngày với màu
                    day_num = item['date'].split('-')[0] if '-' in item['date'] else item['date'][:2]
                    
                    # HTML cho badge ngày
                    badge_html = f"""<div style="display: flex; align-items: center; margin: 10px 0;"><div style="background-color: #c9a0dc; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold; margin-right: 10px; min-width: 40px; text-align: center;">{day_num}</div><div style="color: #888; font-size: 14px;">{item['date']} ({item['source']}): </div></div>"""
                    st.markdown(badge_html, unsafe_allow_html=True)
                    
                    # Hiển thị nhị hợp với màu theo tần suất
                    nhi_hop_html = "<div style='display: flex; flex-wrap: wrap; gap: 5px; margin-left: 50px; margin-bottom: 15px;'>"
                    
                    for num, freq in item['nhi_hop']:
                        # Chọn màu dựa trên tần suất
                        if freq >= 10:
                            bg_color = "#90EE90"  # Xanh lá nhạt
                            text_color = "#006400"  # Xanh đậm
                        elif freq >= 5:
                            bg_color = "#FFD700"  # Vàng
                            text_color = "#8B4513"  # Nâu
                        elif freq >= 2:
                            bg_color = "#FFB6C1"  # Hồng nhạt
                            text_color = "#8B0000"  # Đỏ đậm
                        else:
                            bg_color = "#E0E0E0"  # Xám nhạt
                            text_color = "#404040"  # Xám đậm
                        
                        nhi_hop_html += f"<span style='background-color: {bg_color}; color: {text_color}; padding: 3px 8px; border-radius: 3px; font-weight: 500; font-size: 14px; display: inline-block;'>{num}</span>"
                    
                    nhi_hop_html += "</div>"
                    st.markdown(nhi_hop_html, unsafe_allow_html=True)
                
                # === THỐNG KÊ MỨC SỐ ===
                st.markdown("---")
                st.markdown("### 📊 THỐNG KÊ MỨC SỐ")
                st.caption("Gom các số theo tần suất xuất hiện (Trùng với ĐB/G1 mới nhất)")
                
                # Tạo DataFrame tần suất
                df_freq = pd.DataFrame([
                    {"Số": k, "Tần suất": v}
                    for k, v in all_nhi_hop_freq.items()
                ])
                df_freq = df_freq.sort_values('Tần suất', ascending=False)
                
                # Gom theo mức (cùng tần suất)
                from collections import defaultdict
                level_groups = defaultdict(list)
                for _, row in df_freq.iterrows():
                    freq = row['Tần suất']
                    level_groups[freq].append(row['Số'])
                
                # Hiển thị theo mức với màu sắc
                for freq in sorted(level_groups.keys(), reverse=True):
                    nums = sorted(level_groups[freq])
                    count = len(nums)
                    
                    # Chọn màu
                    if freq >= 10:
                        bg_color = "#d4edda"
                        text_color = "#155724"
                        icon = "🟢"
                    elif freq >= 5:
                        bg_color = "#fff3cd"
                        text_color = "#856404"
                        icon = "🟡"
                    elif freq >= 2:
                        bg_color = "#f8d7da"
                        text_color = "#721c24"
                        icon = "🔴"
                    else:
                        bg_color = "#e2e3e5"
                        text_color = "#383d41"
                        icon = "⚪"
                    
                    # HTML cho mỗi mức
                    level_html = f"""
                    <div style="background-color: {bg_color}; padding: 10px; margin: 8px 0; 
                                border-radius: 5px; border-left: 4px solid {text_color};">
                        <div style="color: {text_color}; font-weight: bold; margin-bottom: 5px;">
                            {icon} Mức {freq} ({count} số):
                        </div>
                        <div style="color: {text_color}; font-size: 16px; font-weight: 500;">
                            {', '.join(nums)}
                        </div>
                    </div>
                    """
                    st.markdown(level_html, unsafe_allow_html=True)
                
                # Chú thích
                st.caption("""
                **Chú thích:**
                - 🟢 Mức ≥10: Số HOT (xuất hiện nhiều)
                - 🟡 Mức 5-9: Trung bình
                - 🔴 Mức 2-4: Ít xuất hiện
                - ⚪ Mức 0-1: Số GAN (rất ít hoặc chưa từng về)
                """)
                
                # Thống kê tổng
                st.markdown("---")
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                col_stat1.metric("Tổng số nhị hợp", len(all_nhi_hop_freq))
                col_stat2.metric("Số HOT (≥10)", len([f for f in all_nhi_hop_freq.values() if f >= 10]))
                col_stat3.metric("Số GAN (0-1)", len([f for f in all_nhi_hop_freq.values() if f <= 1]))
                
                # Biểu đồ phân bố
                st.markdown("---")
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    import plotly.graph_objects as go
                    # Top 20 số có tần suất cao nhất
                    top_20 = df_freq.head(20)
                    fig1 = go.Figure(data=[
                        go.Bar(x=top_20['Số'], y=top_20['Tần suất'],
                               marker_color='lightblue',
                               text=top_20['Tần suất'],
                               textposition='auto')
                    ])
                    fig1.update_layout(title="Top 20 Số Hot Nhất",
                                      xaxis_title="Số",
                                      yaxis_title="Tần suất",
                                      height=350)
                    st.plotly_chart(fig1, use_container_width=True)
                
                with col_chart2:
                    # Phân bố theo mức tần suất
                    level_data = pd.DataFrame([
                        {"Mức": f"Mức {freq}", "Số lượng": len(nums)}
                        for freq, nums in sorted(level_groups.items(), reverse=True)
                    ])
                    fig2 = go.Figure(data=[
                        go.Bar(x=level_data['Mức'],
                               y=level_data['Số lượng'],
                               marker_color='lightcoral',
                               text=level_data['Số lượng'],
                               textposition='auto')
                    ])
                    fig2.update_layout(title="Phân Bố Theo Mức Tần Suất",
                                      xaxis_title="Mức",
                                      yaxis_title="Số lượng số",
                                      height=350)
                    st.plotly_chart(fig2, use_container_width=True)
                
                # Export
                csv_nhi_hop = df_freq.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Tải xuống Nhị Hợp & Tần Suất (CSV)",
                    data=csv_nhi_hop,
                    file_name=f"nhi_hop_tan_suat_{src_mode}_{comp_mode}.csv",
                    mime="text/csv"
                )
                
            else:
                st.info("✅ Tất cả các dàn đều đã nổ ít nhất 1 lần!")


# === TAB 3: BỆT CẦU ===
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
