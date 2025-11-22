from itertools import combinations
from typing import List, Dict, Tuple, Set
import pandas as pd
from collections import Counter, defaultdict

# --- TỪ ĐIỂN DỮ LIỆU ---
BO_DICT = {
    "00": ["00","55","05","50"], "11": ["11","66","16","61"], "22": ["22","77","27","72"], "33": ["33","88","38","83"],
    "44": ["44","99","49","94"], "01": ["01","10","06","60","51","15","56","65"], "02": ["02","20","07","70","25","52","57","75"],
    "03": ["03","30","08","80","35","53","58","85"], "04": ["04","40","09","90","45","54","59","95"], "12": ["12","21","17","71","26","62","67","76"],
    "13": ["13","31","18","81","36","63","68","86"], "14": ["14","41","19","91","46","64","69","96"], "23": ["23","32","28","82","73","37","78","87"],
    "24": ["24","42","29","92","74","47","79","97"], "34": ["34","43","39","93","84","48","89","98"]
}
# Tạo map ngược để tra cứu siêu tốc O(1)
REVERSE_BO = {v: k for k, vals in BO_DICT.items() for v in vals}

KEP_DICT = {
    "K.AM": ["07","70","14","41","29","92","36","63","58","85"],
    "K.BANG": ["00","11","22","33","44","55","66","77","88","99"],
    "K.LECH": ["05","50","16","61","27","72","38","83","49","94"],
    "S.KEP": ["01","10","12","21","23","32","34","43","45","54","56","65","67","76","78","87","89","98","09","90"]
}

# --- HÀM TRA CỨU ---
def bo(db: str) -> str:
    if not db: return "??"
    return REVERSE_BO.get(db.zfill(2), "44")

def kep(db: str) -> str:
    db = db.zfill(2)
    for key, vals in KEP_DICT.items():
        if db in vals: return key
    return "-"

# --- LOGIC NÂNG CAO ---
def tim_chu_so_bet(d1, d2, kieu):
    """Tìm chữ số bệt giữa 2 dãy số (list hoặc str)"""
    d1, d2 = list(str(d1)), list(str(d2))
    bet = []
    min_len = min(len(d1), len(d2))
    
    if kieu == "Bệt Phải": 
        for i in range(min_len - 1):
            if d1[i] == d2[i + 1]: bet.append(d1[i])
    elif kieu == "Thẳng": 
        for i in range(min_len):
            if d1[i] == d2[i]: bet.append(d1[i])
    elif kieu == "Bệt trái": 
        for i in range(1, min_len):
            if d1[i] == d2[i - 1]: bet.append(d1[i])
    return sorted(set(bet))

def lay_dan_cham(chuoi_cham):
    res = set()
    for i in range(100):
        pair = f"{i:02d}"
        for c in chuoi_cham:
            if c in pair: res.add(pair); break
    return sorted(res)

def lay_nhi_hop(bet_digits, digits_2_dong):
    unique_digits = sorted(set(digits_2_dong))
    nh = set()
    for a, b in combinations(unique_digits, 2):
        if a in bet_digits or b in bet_digits:
            nh.add(a + b); nh.add(b + a)
    return sorted(nh)

# --- CÔNG CỤ THÔNG MINH MỚI ---

def phan_tich_tan_suat(df: pd.DataFrame, col_name: str, top_n: int = 20) -> Dict[str, int]:
    """
    Phân tích tần suất xuất hiện của các số 2 chữ số.
    
    Args:
        df: DataFrame chứa dữ liệu
        col_name: Tên cột cần phân tích (vd: 'xsmb_2so', 'g1_2so')
        top_n: Số lượng kết quả trả về
        
    Returns:
        Dictionary với key là số, value là số lần xuất hiện
    """
    numbers = df[col_name].dropna().astype(str).str.zfill(2)
    counter = Counter(numbers)
    return dict(counter.most_common(top_n))

def tim_chu_ky(df: pd.DataFrame, so_can_tim: str, col_name: str) -> Dict:
    """
    Tìm chu kỳ xuất hiện của một số cụ thể.
    
    Args:
        df: DataFrame chứa dữ liệu (đã sắp xếp theo ngày mới nhất trước)
        so_can_tim: Số cần tìm (2 chữ số)
        col_name: Tên cột cần tìm
        
    Returns:
        Dictionary chứa thông tin chu kỳ
    """
    so_can_tim = so_can_tim.zfill(2)
    indices = []
    
    for idx, row in df.iterrows():
        val = str(row[col_name]).zfill(2) if pd.notna(row[col_name]) else ""
        if val == so_can_tim:
            indices.append(idx)
    
    if len(indices) < 2:
        return {
            "so_lan_xuat_hien": len(indices),
            "chu_ky_trung_binh": None,
            "khoang_cach": [],
            "du_doan_ngay_tiep_theo": None
        }
    
    # Tính khoảng cách giữa các lần xuất hiện
    gaps = [indices[i] - indices[i+1] for i in range(len(indices)-1)]
    avg_gap = sum(gaps) / len(gaps) if gaps else 0
    
    # Dự đoán ngày xuất hiện tiếp theo
    next_index = max(0, indices[0] - int(avg_gap))
    
    return {
        "so_lan_xuat_hien": len(indices),
        "chu_ky_trung_binh": round(avg_gap, 1),
        "khoang_cach": gaps,
        "chi_so_du_doan": next_index,
        "lan_gan_nhat": indices[0] if indices else None
    }

def phan_tich_pattern(df: pd.DataFrame, col_name: str, min_length: int = 2) -> List[Dict]:
    """
    Tìm các pattern số lặp lại (chuỗi số xuất hiện liên tiếp).
    
    Args:
        df: DataFrame chứa dữ liệu
        col_name: Tên cột cần phân tích
        min_length: Độ dài tối thiểu của pattern
        
    Returns:
        List các pattern tìm được
    """
    numbers = df[col_name].dropna().astype(str).str.zfill(2).tolist()
    patterns = defaultdict(list)
    
    # Tìm pattern độ dài 2-4
    for length in range(min_length, min(5, len(numbers))):
        for i in range(len(numbers) - length + 1):
            pattern = tuple(numbers[i:i+length])
            patterns[pattern].append(i)
    
    # Lọc pattern xuất hiện >= 2 lần
    result = []
    for pattern, positions in patterns.items():
        if len(positions) >= 2:
            result.append({
                "pattern": " → ".join(pattern),
                "do_dai": len(pattern),
                "so_lan": len(positions),
                "vi_tri": positions[:5]  # Chỉ lấy 5 vị trí đầu
            })
    
    # Sắp xếp theo số lần xuất hiện
    result.sort(key=lambda x: x["so_lan"], reverse=True)
    return result[:20]  # Top 20 patterns

def du_doan_bo_so(df: pd.DataFrame, col_name: str, top_n: int = 10) -> List[Dict]:
    """
    Dự đoán bộ số có khả năng xuất hiện dựa trên phân tích lịch sử.
    
    Args:
        df: DataFrame chứa dữ liệu
        col_name: Tên cột cần phân tích
        top_n: Số lượng dự đoán
        
    Returns:
        List các bộ số được đề xuất với độ tin cậy
    """
    # Phân tích tần suất
    freq = phan_tich_tan_suat(df, col_name, 100)
    
    # Phân tích chu kỳ cho các số hot
    predictions = []
    for num, count in list(freq.items())[:30]:
        cycle_info = tim_chu_ky(df, num, col_name)
        
        if cycle_info["chu_ky_trung_binh"] and cycle_info["lan_gan_nhat"] is not None:
            # Tính điểm dựa trên tần suất và chu kỳ
            days_since_last = cycle_info["lan_gan_nhat"]
            avg_cycle = cycle_info["chu_ky_trung_binh"]
            
            # Nếu gần đến chu kỳ thì điểm cao hơn
            if days_since_last >= avg_cycle * 0.7:
                confidence = min(95, (days_since_last / avg_cycle) * 50 + (count / max(freq.values())) * 50)
                predictions.append({
                    "so": num,
                    "tan_suat": count,
                    "chu_ky_TB": avg_cycle,
                    "ngay_chua_ve": days_since_last,
                    "do_tin_cay": round(confidence, 1)
                })
    
    # Sắp xếp theo độ tin cậy
    predictions.sort(key=lambda x: x["do_tin_cay"], reverse=True)
    return predictions[:top_n]

def thong_ke_cap_so(df: pd.DataFrame, col1: str, col2: str) -> List[Dict]:
    """
    Phân tích các cặp số thường xuất hiện cùng nhau (correlation).
    
    Args:
        df: DataFrame chứa dữ liệu
        col1: Cột thứ nhất (vd: 'xsmb_2so')
        col2: Cột thứ hai (vd: 'g1_2so')
        
    Returns:
        List các cặp số xuất hiện cùng nhau
    """
    pairs = defaultdict(int)
    
    for _, row in df.iterrows():
        val1 = str(row[col1]).zfill(2) if pd.notna(row[col1]) else None
        val2 = str(row[col2]).zfill(2) if pd.notna(row[col2]) else None
        
        if val1 and val2:
            pair = tuple(sorted([val1, val2]))
            pairs[pair] += 1
    
    result = [
        {"cap": f"{p[0]} - {p[1]}", "so_lan": count}
        for p, count in pairs.items()
        if count >= 2
    ]
    
    result.sort(key=lambda x: x["so_lan"], reverse=True)
    return result[:20]

