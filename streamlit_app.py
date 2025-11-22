import streamlit as st
import pandas as pd
import logic
import data_fetcher
import concurrent.futures

st.set_page_config(page_title="SIÊU GÀ APP", page_icon="🐔", layout="wide")

# --- STYLE ---
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 5px; }
    .stTabs [data-baseweb="tab"] { background-color: #f0f2f6; border-radius: 5px; padding: 10px; }
    .stTabs [aria-selected="true"] { background-color: #fff; border-top: 3px solid #ff4b4b; }
</style>
""", unsafe_allow_html=True)

# --- HÀM TẢI DỮ LIỆU CHÍNH ---
@st.cache_data(ttl=600)
def load_data(days):
    # Tải song song 3 nguồn
    with concurrent.futures.ThreadPoolExecutor() as executor:
        f_dt = executor.submit(data_fetcher.fetch_dien_toan, days)
        f_tt = executor.submit(data_fetcher.fetch_than_tai, days)
        f_mb = executor.submit(data_fetcher.fetch_xsmb_group, days)
        
        dt = f_dt.result()
        tt = f_tt.result()
        mb_db, mb_g1 = f_mb.result()
    
    # Xử lý dữ liệu thành DataFrame
    df_dt = pd.DataFrame(dt)
    df_tt = pd.DataFrame(tt)
    
    # Ghép XSMB vào ngày của Điện toán (để khớp ngày)
    xsmb_rows = []
    min_len = min(len(dt), len(mb_db), len(mb_g1))
    
    for i in range(min_len):
        xsmb_rows.append({
            "date": dt[i]["date"], # Lấy ngày từ nguồn Điện toán
            "xsmb_full": mb_db[i],
            "xsmb_2so": mb_db[i][-2:],
            "g1_full": mb_g1[i],
            "g1_2so": mb_g1[i][-2:]
        })
    df_xsmb = pd.DataFrame(xsmb_rows)
    
    # Gộp tất cả lại
    if not df_dt.empty and not df_xsmb.empty:
        df = pd.merge(df_dt, df_tt, on="date", how="left")
        df = pd.merge(df, df_xsmb, on="date", how="left")
        return df
    return pd.DataFrame()

# --- GIAO DIỆN ---
with st.sidebar:
    st.title("🐔 SIÊU GÀ TOOL")
    days_fetch = st.number_input("Số ngày tải:", 30, 100, 60)
    if st.button("🔄 TẢI DỮ LIỆU", type="primary"):
        st.cache_data.clear()
        st.rerun()

# Tải dữ liệu
try:
    with st.spinner("Đang tải dữ liệu..."):
        df = load_data(days_fetch)
        if df.empty:
            st.error("Lỗi: Không tải được dữ liệu. Kiểm tra mạng!")
            st.stop()
except Exception as e:
    st.error(f"Có lỗi xảy ra: {e}")
    st.stop()

# Hiển thị
tabs = st.tabs(["KẾT QUẢ", "DÀN NUÔI", "TRA CỨU"])

with tabs[0]:
    st.subheader("Bảng Kết Quả Tổng Hợp")
    df_show = df.copy()
    df_show["Điện Toán"] = df_show["dt_numbers"].apply(lambda x: " - ".join(x) if isinstance(x, list) else "")
    st.dataframe(
        df_show[["date", "Điện Toán", "tt_number", "xsmb_full", "g1_full"]],
        column_config={"date": "Ngày", "tt_number": "Thần Tài", "xsmb_full": "Đặc Biệt", "g1_full": "Giải Nhất"},
        hide_index=True, use_container_width=True
    )

with tabs[1]:
    st.subheader("Phân Tích Dàn Nuôi")
    c1, c2 = st.columns(2)
    src = c1.selectbox("Nguồn:", ["Thần Tài", "Điện Toán"])
    khung = c2.slider("Khung ngày:", 1, 20, 5)
    
    if st.button("Soi Cầu"):
        kq = []
        for i in range(len(df)):
            row = df.iloc[i]
            # Lấy số nguồn
            src_nums = ""
            if src == "Thần Tài": src_nums = str(row.get("tt_number", ""))
            else: src_nums = "".join(row.get("dt_numbers", []))
            
            if not src_nums: continue
            
            # Tạo dàn
            s = set(src_nums)
            dan = {a+b for a in s for b in s}
            
            # Check ăn
            an = False
            ngay_an = ""
            for k in range(1, khung + 1):
                if i - k >= 0:
                    res = df.iloc[i-k]["xsmb_2so"]
                    if res in dan:
                        an = True
                        ngay_an = f"Ngày {k}"
                        break
            
            kq.append({
                "Ngày": row["date"],
                "Nguồn": src_nums,
                "Dàn": " ".join(sorted(dan)),
                "Kết Quả": f"✅ Ăn {ngay_an}" if an else "❌ Trượt"
            })
            
        st.dataframe(pd.DataFrame(kq), use_container_width=True)

with tabs[2]:
    st.subheader("Tra Cứu Số")
    find = st.text_input("Nhập số (VD: 68):")
    if find:
        mask = df.apply(lambda r: find in str(r["xsmb_full"]) or find in str(r["g1_full"]), axis=1)
        st.dataframe(df[mask][["date", "xsmb_full", "g1_full"]], use_container_width=True)
