from itertools import combinations

# --- TỪ ĐIỂN DỮ LIỆU ---
BO_DICT = {
    "00": ["00","55","05","50"], "11": ["11","66","16","61"], "22": ["22","77","27","72"], "33": ["33","88","38","83"],
    "44": ["44","99","49","94"], "01": ["01","10","06","60","51","15","56","65"], "02": ["02","20","07","70","25","52","57","75"],
    "03": ["03","30","08","80","35","53","58","85"], "04": ["04","40","09","90","45","54","59","95"], "12": ["12","21","17","71","26","62","67","76"],
    "13": ["13","31","18","81","36","63","68","86"], "14": ["14","41","19","91","46","64","69","96"], "23": ["23","32","28","82","73","37","78","87"],
    "24": ["24","42","29","92","74","47","79","97"], "34": ["34","43","39","93","84","48","89","98"]
}

KEP_DICT = {
    "K.AM": ["07","70","14","41","29","92","36","63","58","85"],
    "K.BANG": ["00","11","22","33","44","55","66","77","88","99"],
    "K.LECH": ["05","50","16","61","27","72","38","83","49","94"],
    "S.KEP": ["01","10","12","21","23","32","34","43","45","54","56","65","67","76","78","87","89","98","09","90"]
}

ZODIAC_DICT = {
    "Tý":   ["00","12","24","36","48","60","72","84","96"],
    "Sửu":  ["01","13","25","37","49","61","73","85","97"],
    "Dần":  ["02","14","26","38","50","62","74","86","98"],
    "Mão":  ["03","15","27","39","51","63","75","87","99"],
    "Thìn": ["04","16","28","40","52","64","76","88"],
    "Tỵ":   ["05","17","29","41","53","65","77","89"],
    "Ngọ":  ["06","18","30","42","54","66","78","90"],
    "Mùi":  ["07","19","31","43","55","67","79","91"],
    "Thân": ["08","20","32","44","56","68","80","92"],
    "Dậu":  ["09","21","33","45","57","69","81","93"],
    "Tuất": ["10","22","34","46","58","70","82","94"],
    "Hợi":  ["11","23","35","47","59","71","83","95"]
}

# --- CÁC HÀM TRA CỨU CƠ BẢN ---
def bo(db: str) -> str:
    db = db.zfill(2)
    if db in BO_DICT: return db
    for key, vals in BO_DICT.items():
        if db in vals: return key
    return "44"

def kep(db: str) -> str:
    db = db.zfill(2)
    for key, vals in KEP_DICT.items():
        if db in vals: return key
    return "-"

def hieu(pair: str) -> int:
    p = pair.zfill(2)
    hieu_map = {
        0:  ["00","11","22","33","44","55","66","77","88","99"],
        1:  ["09","10","21","32","43","54","65","76","87","98"],
        2:  ["08","19","20","31","42","53","64","75","86","97"],
        3:  ["07","18","29","30","41","52","63","74","85","96"],
        4:  ["06","17","28","39","40","51","62","73","84","95"],
        5:  ["05","16","27","38","49","50","61","72","83","94"],
        6:  ["04","15","26","37","48","59","60","71","82","93"],
        7:  ["03","14","25","36","47","58","69","70","81","92"],
        8:  ["02","13","24","35","46","57","68","79","80","91"],
        9:  ["01","12","23","34","45","56","67","78","89","90"],
    }
    for delay, nums in hieu_map.items():
        if p in nums: return delay
    return -1

def zodiac(pair: str) -> str:
    p = pair.zfill(2)
    return next((a for a, lst in ZODIAC_DICT.items() if p in lst), "-")

# --- CÁC HÀM HỖ TRỢ HIỂN THỊ ---
def doc_so_chu(so):
    """Chuyển số thành chữ (VD: 85 -> tám năm)"""
    so = str(so)
    map_chu = {
        "0": "không", "1": "một", "2": "hai", "3": "ba", "4": "bốn",
        "5": "năm", "6": "sáu", "7": "bảy", "8": "tám", "9": "chín"
    }
    return " ".join([map_chu.get(c, c) for c in so])

def get_bo_dan(bo_val):
    return ", ".join(BO_DICT.get(bo_val, []))

def get_kep_dan(kep_val):
    return ", ".join(KEP_DICT.get(kep_val, []))

def get_zodiac_dan(z_val):
    return ", ".join(ZODIAC_DICT.get(z_val, []))

def get_tong_dan(tong_val):
    tong_val = int(tong_val)
    res = [f"{i:02d}" for i in range(100) if (int(f"{i:02d}"[0]) + int(f"{i:02d}"[1])) % 10 == tong_val]
    return ", ".join(res)

def get_hieu_dan(hieu_val):
    try:
        h = int(hieu_val)
        hieu_map = {
            0:  ["00","11","22","33","44","55","66","77","88","99"],
            1:  ["09","10","21","32","43","54","65","76","87","98"],
            2:  ["08","19","20","31","42","53","64","75","86","97"],
            3:  ["07","18","29","30","41","52","63","74","85","96"],
            4:  ["06","17","28","39","40","51","62","73","84","95"],
            5:  ["05","16","27","38","49","50","61","72","83","94"],
            6:  ["04","15","26","37","48","59","60","71","82","93"],
            7:  ["03","14","25","36","47","58","69","70","81","92"],
            8:  ["02","13","24","35","46","57","68","79","80","91"],
            9:  ["01","12","23","34","45","56","67","78","89","90"]
        }
        return ", ".join(hieu_map.get(h, []))
    except: return ""

# --- CÁC HÀM MỚI THÊM (ĐẦU/ĐUÔI GAN) ---
def get_dau_dan(dau_val):
    """Trả về dàn số theo đầu (VD: đầu 1 -> 10,11...19)"""
    return ", ".join([f"{dau_val}{i}" for i in range(10)])

def get_duoi_dan(duoi_val):
    """Trả về dàn số theo đuôi (VD: đuôi 5 -> 05,15...95)"""
    return ", ".join([f"{i}{duoi_val}" for i in range(10)])

# --- CÁC HÀM LOGIC NÂNG CAO ---
def tim_chu_so_bet(d1, d2, kieu):
    """Tìm chữ số bệt giữa 2 dãy số"""
    bet = []
    if kieu == "Bệt Phải": # So sánh chéo: d1[i] == d2[i+1]
        for i in range(min(len(d1) - 1, len(d2))):
            if d1[i] == d2[i + 1]: bet.append(d1[i])
    elif kieu == "Thẳng": # So sánh thẳng: d1[i] == d2[i]
        for i in range(min(len(d1), len(d2))):
            if d1[i] == d2[i]: bet.append(d1[i])
    elif kieu == "Bệt trái": # So sánh chéo ngược: d1[i] == d2[i-1]
        for i in range(1, min(len(d1), len(d2) + 1)):
            if d1[i] == d2[i - 1]: bet.append(d1[i])
    return sorted(set(bet))

def lay_dan_cham(chuoi_cham):
    """Tạo dàn số từ các chạm"""
    res = []
    for i in range(100):
        pair = f"{i:02d}"
        for c in chuoi_cham:
            if c in pair:
                res.append(pair)
                break
    return sorted(set(res))

def lay_nhi_hop(bet_digits, digits_2_dong):
    """Tạo dàn nhị hợp"""
    unique_digits = sorted(set(digits_2_dong))
    nh = []
    for a, b in combinations(unique_digits, 2):
        if a in bet_digits or b in bet_digits:
            nh += [a + b, b + a]
    return sorted(set(nh))
