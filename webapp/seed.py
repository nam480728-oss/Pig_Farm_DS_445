"""Tạo dữ liệu giả lập để làm giao diện khi chưa có mô hình thật.

Chạy:  python seed.py        (xoá DB cũ, tạo lại)
"""
import json
import random

import cv2
import numpy as np
from datetime import datetime, timedelta

import db

random.seed(7)
NOW = datetime(2026, 11, 1, 8, 0, 0)


def tao_anh_camera(ma, n):
    """Ảnh giả: sàn chuồng + các hình bầu dục như lợn, để có ảnh nền vẽ vùng."""
    img = np.full((540, 960, 3), (150, 160, 150), np.uint8)
    cv2.rectangle(img, (80, 60), (880, 480), (120, 130, 120), 6)
    for _ in range(n):
        c = (random.randint(150, 800), random.randint(100, 440))
        cv2.ellipse(img, c, (45, 24), random.randint(0, 180), 0, 360, (190, 170, 200), -1)
    cv2.putText(img, f"O {ma} (anh gia lap)", (20, 36), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imwrite(str(db.DB_PATH.parent / "camera" / f"{ma}.jpg"), img)


def tao_anh_con(duong_dan, ten, kg):
    img = np.full((90, 120, 3), (140, 150, 140), np.uint8)
    cv2.ellipse(img, (60, 48), (40, 22), 0, 0, 360, (190, 170, 200), -1)
    cv2.putText(img, f"{ten} {kg:.0f}kg", (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    cv2.imwrite(str(db.DB_PATH.parent / duong_dan), img)


def main():
    (db.DB_PATH.parent / "camera").mkdir(parents=True, exist_ok=True)
    if db.DB_PATH.exists():
        db.DB_PATH.unlink()
    db.init_db()
    with db.connect() as c:
        o_list = [("A", "Ô A – lợn thịt", 20), ("B", "Ô B – lợn thịt", 18),
                  ("C", "Ô C – lợn con", 25), ("D", "Ô D – nái hậu bị", 8)]
        for ma, ten, n in o_list:
            c.execute("INSERT INTO o_chuong(ma,ten,so_dang_ky,camera) VALUES (?,?,?,?)",
                      (ma, ten, n, f"videos/o_{ma.lower()}.mp4"))
            tao_anh_camera(ma, n)

        dan = [("D01", "A", 20, "2026-08-15", 32.0, 0.7), ("D02", "B", 18, "2026-09-01", 28.5, 0.7),
               ("D03", "C", 25, "2026-10-10", 9.0, 0.4)]
        for d in dan:
            c.execute("INSERT INTO dan(ma,o,so_con,ngay_nhap,kg_nhap_tb,moc_kg_ngay) VALUES (?,?,?,?,?,?)", d)

        # Lần đo hằng tuần (từ sau ngày nhập). kg = kg nhập + tốc độ × số ngày + lệch riêng từng con.
        # Con số 1 là con còi, con số 2 lớn nhanh -> để báo cáo có dữ liệu thử.
        (db.DB_PATH.parent / "recordings" / "con").mkdir(parents=True, exist_ok=True)
        for ma, o, n, nhap, kg0, moc in dan:
            ngay_nhap = datetime.fromisoformat(nhap)
            for i in range(n):
                toc_do = random.gauss(moc, 0.03)
                if i == 0: toc_do = moc * 0.7
                if i == 1: toc_do = moc * 1.3
                lech = random.gauss(0, 1.5)
                lan = [NOW - timedelta(days=7 * k) for k in range(4, -1, -1)]
                lan = [t for t in lan if t > ngay_nhap]
                for j, t in enumerate(lan):
                    kg = kg0 + lech + toc_do * (t - ngay_nhap).days
                    anh = None
                    if j == len(lan) - 1:
                        anh = f"recordings/con/{ma}-{i+1:02d}.jpg"
                        tao_anh_con(anh, f"{ma}-{i+1:02d}", kg)
                    c.execute("INSERT INTO lan_do(dan,con_id,thoi_gian,kg,anh) VALUES (?,?,?,?,?)",
                              (ma, f"{ma}-{i+1:02d}", t.isoformat(), round(kg, 1), anh))

        su_kien = [
            ("nghi_trom", "A", -3, "khan_cap", {"so_nguoi": 1, "khung": 14}),
            ("lac_chuong", "B", -10, "khan_cap", {"id_theo_doi": 12, "giay_ngoai": 6}),
            ("dem_thieu", "C", -26, "canh_bao", {"dem": 23, "dang_ky": 25}),
            ("dem_du", "A", -26, "thong_tin", {"dem": 20, "dang_ky": 20}),
            ("tho_nhanh", "D", -30, "canh_bao", {"nhip": 52, "gio_nam": 4}),
            ("bo_an", "B", -31, "canh_bao", {"diem_nghi_van": 0.8}),
            ("nguoi_la", "A", -50, "canh_bao", {"khung": 12}),
            ("nghi_chet", "C", -52, "khan_cap", {"nhip": None, "gio_nam": 4}),
            ("o_an_kem", "B", -75, "canh_bao", {"ty_le_an": 0.45}),
            ("dem_du", "B", -98, "thong_tin", {"dem": 18, "dang_ky": 18}),
            ("lac_chuong", "A", -120, "khan_cap", {"id_theo_doi": 3, "giay_ngoai": 9}),
            ("nguoi_la", "D", -140, "canh_bao", {"khung": 15}),
        ]
        for loai, o, gio, muc, dl in su_kien:
            t = NOW + timedelta(hours=gio / 10 * 1.0)  # rải đều quanh hôm nay
            c.execute("INSERT INTO su_kien(loai,o,thoi_gian,muc,anh,du_lieu) VALUES (?,?,?,?,?,?)",
                      (loai, o, t.replace(microsecond=0).isoformat(), muc, None,
                       json.dumps(dl, ensure_ascii=False)))
    print("Đã tạo dữ liệu giả lập:", db.DB_PATH)


if __name__ == "__main__":
    main()
