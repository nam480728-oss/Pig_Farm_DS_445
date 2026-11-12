"""Kiểm thử toàn hệ thống (chạy trên DB tạm, không đụng dữ liệu thật):  python kiem_thu.py

Đóng vai TV2/TV4/TV5: gửi mọi loại sự kiện, ghi lần đo, đọc vùng, chạy video, rồi kiểm tra
webapp xử lý đúng. Đưa cho cả nhóm chạy trước buổi demo.
"""
import os
import sys
import tempfile
import time

os.environ["TT_DATA"] = tempfile.mkdtemp(prefix="tt_test_")
import cv2
import numpy as np

import app as webapp
import events
import seed

seed.main()
c = webapp.app.test_client()
loi = []


def kiem(ten, dieu_kien, chi_tiet=""):
    print(("  OK  " if dieu_kien else " LỖI ") + ten + (f"  [{chi_tiet}]" if chi_tiet and not dieu_kien else ""))
    if not dieu_kien:
        loi.append(ten)


print("1. Các trang")
for p in ["/", "/o-chuong", "/dan", "/dan/D01", "/dan/D01?tab=coi", "/su-kien", "/cai-dat", "/ve-vung", "/ve-vung/A", "/chay-video"]:
    kiem(f"GET {p}", c.get(p).status_code == 200)

print("2. Gửi đủ các loại sự kiện (mục 8) và quyết định banner")
MAU = {"nghi_trom": "khan_cap", "lac_chuong": "khan_cap", "nghi_chet": "khan_cap", "dem_thieu": "canh_bao",
       "tho_nhanh": "canh_bao", "bo_an": "canh_bao", "o_an_kem": "canh_bao", "dem_du": "thong_tin"}
dau = c.get("/api/thong-bao").get_json()["moi_nhat"]
for loai, muc in MAU.items():
    r = c.post("/api/su-kien", json={"loai": loai, "o": "A", "muc": muc, "thoi_gian": "2026-11-10T12:00:00",
                                      "du_lieu": {"nhip": None, "gio_nam": 4} if loai == "nghi_chet" else {}})
    kiem(f"nhận {loai}", r.status_code == 201, r.get_data(as_text=True))
hien = {e["loai"] for e in c.get(f"/api/thong-bao?sau={dau}").get_json()["ds"]}
kiem("banner hiện đúng loại cần hiện", hien == set(MAU) - {"dem_du"}, str(hien))
kiem("nguoi_la ban ngày chỉ lưu, không banner",
     c.post("/api/su-kien", json={"loai": "nguoi_la", "o": "B", "muc": "canh_bao", "thoi_gian": "2026-11-10T12:00:00"}).get_json()["hien_ngay"] is False)
kiem("nguoi_la ban đêm có banner",
     c.post("/api/su-kien", json={"loai": "nguoi_la", "o": "B", "muc": "canh_bao", "thoi_gian": "2026-11-10T23:30:00"}).get_json()["hien_ngay"] is True)
kiem("từ chối sự kiện sai", c.post("/api/su-kien", json={"loai": "x", "o": "A", "muc": "y", "thoi_gian": "z"}).status_code == 400)
kiem("nghi_chet hiện dữ liệu nhịp thở", "Nhịp thở" in c.get("/su-kien").get_data(as_text=True))

print("3. Lần đo và báo cáo phát triển")
r = c.post("/api/lan-do", json={"dan": "D02", "thoi_gian": "2026-11-08T08:00:00",
                                "ds": [{"con_id": f"D02-{i:02d}", "kg": 60 + i} for i in range(1, 19)]})
kiem("ghi lần đo", r.status_code == 201)
bc = c.get("/api/dan/D02/bao-cao").get_json()
kiem("báo cáo có đủ trường", all(k in bc for k in ("tb_kg", "tang_kg", "tang_pct", "dong_deu_pct", "con_coi", "con_lon_nhanh")))
kiem("lần đo sai bị từ chối", c.post("/api/lan-do", json={"dan": "D02", "thoi_gian": "2026-11-08T08:00:00", "ds": [{"con_id": "a", "kg": 9999}]}).status_code == 400)

print("4. Vùng và chạy video (MOCK nếu chưa có ai/pipeline.py)")
v = {"o": [[.1, .1], [.9, .1], [.9, .9]], "lac_chuong": {"kieu": "vung", "diem": [[0, 0], [.1, 0], [.1, .1]]}}
kiem("lưu vùng", c.put("/api/o/B/vung", json=v).status_code == 200)
kiem("đọc vùng pixel", "o" in c.get("/api/o/B/vung?pixel=1&rong=1920&cao=1080").get_json())
tam = os.path.join(os.environ["TT_DATA"], "clip_lac.mp4")
w = cv2.VideoWriter(tam, cv2.VideoWriter_fourcc(*"mp4v"), 10, (640, 360))
for _ in range(20):
    w.write(np.full((360, 640, 3), 100, np.uint8))
w.release()
with open(tam, "rb") as f:
    job = c.post("/api/chay-video", data={"o": "B", "video": (f, "clip_lac.mp4")}).get_json()["job"]
for _ in range(40):
    st = c.get(f"/api/chay-video/{job}").get_json()
    if st["trang_thai"] != "dang_chay":
        break
    time.sleep(0.5)
kiem("chạy video xong có sự kiện", st["trang_thai"] == "xong" and len(st["ds"]) >= 1, str(st.get("loi")))

print("\n" + ("TẤT CẢ ĐẠT" if not loi else f"{len(loi)} LỖI: {loi}"))
sys.exit(1 if loi else 0)
