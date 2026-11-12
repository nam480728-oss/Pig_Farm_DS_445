"""Phát sự kiện theo kịch bản demo 2 phút, để quay màn hình webapp.

  python seed.py && python app.py      # cửa sổ 1: webapp
  python demo.py                       # cửa sổ 2: bấm Enter đúng lúc bắt đầu quay
  python demo.py --nhanh               # chạy nhanh gấp 10 lần để thử
Kịch bản chi tiết: docs/kich_ban_demo.md
"""
import json
import sys
import time
from datetime import datetime
from urllib import request as rq

import cv2

import db

URL = "http://127.0.0.1:5000/api/su-kien"
NHANH = "--nhanh" in sys.argv
# (giây từ lúc bắt đầu, loại, ô, mức, dữ liệu, có ảnh khoanh đỏ, giờ giả lập)
KICH_BAN = [
    (10,  "dem_du",     "A", "thong_tin", {"dem": 20, "dang_ky": 20}, False, None),
    (25,  "dem_thieu",  "C", "canh_bao",  {"dem": 23, "dang_ky": 25}, True,  None),
    (45,  "lac_chuong", "B", "khan_cap",  {"id_theo_doi": 12, "giay_ngoai": 6}, True, None),
    (65,  "nguoi_la",   "A", "canh_bao",  {"khung": 14}, True, "23:30:00"),   # giả lập ban đêm để có banner
    (80,  "nghi_trom",  "A", "khan_cap",  {"so_nguoi": 1, "khung": 18}, True, "23:31:00"),
    (95,  "tho_nhanh",  "D", "canh_bao",  {"nhip": 52, "gio_nam": 4}, False, None),
    (105, "bo_an",      "B", "canh_bao",  {"diem_nghi_van": 0.8}, False, None),
    (115, "nghi_chet",  "D", "khan_cap",  {"nhip": None, "gio_nam": 4}, True, None),
]


def anh_khoanh_do(o, ten):
    """Lấy ảnh camera của ô, vẽ khung đỏ quanh một con -> data/recordings/su_kien/."""
    nguon = db.DB_PATH.parent / "camera" / f"{o}.jpg"
    img = cv2.imread(str(nguon))
    if img is None:
        return None
    h, w = img.shape[:2]
    cv2.rectangle(img, (w // 3, h // 3), (w // 3 + w // 6, h // 3 + h // 6), (0, 0, 255), 4)
    rel = f"recordings/su_kien/{ten}.jpg"
    (db.DB_PATH.parent / "recordings" / "su_kien").mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(db.DB_PATH.parent / rel), img)
    return rel


def gui(loai, o, muc, dl, co_anh, gio_gia):
    now = datetime.now().replace(microsecond=0)
    tg = now.isoformat() if not gio_gia else f"{now.date()}T{gio_gia}"
    body = {"loai": loai, "o": o, "muc": muc, "du_lieu": dl, "thoi_gian": tg,
            "anh": anh_khoanh_do(o, f"demo_{loai}_{int(time.time())}") if co_anh else None}
    req = rq.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    kq = json.load(rq.urlopen(req))
    print(f"[{time.strftime('%H:%M:%S')}] {loai:11s} ô {o}  banner={'có' if kq['hien_ngay'] else 'không'}")


if __name__ == "__main__":
    input("Sẵn sàng? Bắt đầu quay rồi bấm Enter… ")
    t0 = time.time()
    for giay, *su_kien in KICH_BAN:
        cho = giay / (10 if NHANH else 1) - (time.time() - t0)
        if cho > 0:
            time.sleep(cho)
        gui(*su_kien)
    print("Hết kịch bản.")
