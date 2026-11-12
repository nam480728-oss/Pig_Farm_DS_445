"""Gửi sự kiện giả để thử banner, như TV2/TV4/TV5 sẽ làm.

  python simulate.py              # gửi 1 sự kiện ngẫu nhiên
  python simulate.py lac_chuong   # gửi đúng loại
  python simulate.py --lien tuc   # mỗi 5 giây gửi 1 sự kiện (Ctrl+C để dừng)
"""
import random
import sys
import time
from datetime import datetime
from urllib import request as rq
import json

URL = "http://127.0.0.1:5000/api/su-kien"
MAU = {
    "nghi_trom":  ("khan_cap",  {"so_nguoi": 1, "khung": 14}),
    "lac_chuong": ("khan_cap",  {"id_theo_doi": 12, "giay_ngoai": 6}),
    "nghi_chet":  ("khan_cap",  {"nhip": None, "gio_nam": 4}),
    "dem_thieu":  ("canh_bao",  {"dem": 23, "dang_ky": 25}),
    "tho_nhanh":  ("canh_bao",  {"nhip": 52, "gio_nam": 4}),
    "bo_an":      ("canh_bao",  {"diem_nghi_van": 0.8}),
    "nguoi_la":   ("canh_bao",  {"khung": 12}),
    "dem_du":     ("thong_tin", {"dem": 20, "dang_ky": 20}),
}


def gui(loai):
    muc, dl = MAU[loai]
    body = {"loai": loai, "o": random.choice("ABCD"), "muc": muc, "du_lieu": dl,
            "thoi_gian": datetime.now().replace(microsecond=0).isoformat()}
    req = rq.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    print(loai, "->", rq.urlopen(req).read().decode().strip())


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--lien":
        while True:
            gui(random.choice(list(MAU))); time.sleep(5)
    gui(a[0] if a else random.choice(list(MAU)))
