from itertools import combinations

# --- TỪ ĐIỂN DỮ LIỆU ---
BO_DICT = {
    "00": ["00","55","05","50"], "11": ["11","66","16","61"], "22": ["22","77","27","72"], "33": ["33","88","38","83"],
    "44": ["44","99","49","94"], "01": ["01","10","06","60","51","15","56","65"], "02": ["02","20","07","70","25","52","57","75"],
    "03": ["03","30","08","80","35","53","58","85"], "04": ["04","40","09","90","45","54","59","95"], "12": ["12","21","17","71","26","62","67","76"],
    "13": ["13","31","18","81","36","63","68","86"], "14": ["14","41","19","91","46","64","69","96"], "23": ["23","32","28","82","73","37","78","87"],
    "24": ["24","42","29","92","74","47","79","97"], "34": ["34","43","39","93","84","48","89","98"]
}
REVERSE_BO = {v: k for k, vals in BO_DICT.items() for v in vals}

# --- HÀM XỬ LÝ ---
def bo(db: str) -> str:
    if not db or not db.isdigit(): return "??"
    return REVERSE_BO.get(db[-2:], "??")

def tim_chu_so_bet(d1, d2, kieu):
    """Tìm số bệt giữa 2 chuỗi số"""
    if not d1 or not d2: return []
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
