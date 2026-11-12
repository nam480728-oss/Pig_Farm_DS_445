"""Cầu nối webapp <-> pipeline của Thành viên 2 (Nam).

HỢP ĐỒNG ĐỀ XUẤT (cần chốt với Nam; đổi gì sửa file này):

    # ai/pipeline.py
    def chay_video(nguon, o, vung, on_event, tien_do=None):
        '''
        nguon    : đường dẫn file video
        o        : mã ô chuồng, vd "A"
        vung     : dict vùng theo PIXEL của video (xem vung.sang_pixel / docs/ve_vung.md)
        on_event : hàm nhận 1 dict sự kiện đúng định dạng mục 8 (webapp lưu + quyết định banner)
        tien_do  : hàm tuỳ chọn tien_do(0.0..1.0)
        Ảnh khoanh đỏ lưu dưới data/recordings/su_kien/, trường "anh" ghi
        "recordings/su_kien/<tên>.jpg".
        '''

Nếu chưa import được `ai.pipeline` thì chạy BẢN GIẢ (MOCK) để dựng giao diện: phát vài sự kiện mẫu.
"""
import importlib
import random
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

import cv2

import vung as vung_mod

_JOBS, _LOCK = {}, threading.Lock()
ANH_EXT = {".jpg", ".jpeg", ".png"}
VIDEO_EXT = {".mp4", ".avi", ".mov", ".mkv"}


def _pipeline_that():
    try:
        return importlib.import_module("ai.pipeline")
    except ImportError:
        return None


def che_do():
    return "pipeline" if _pipeline_that() else "mock"


# ---------- khung hình làm ảnh nền ----------
def lay_khung_dau(video_path):
    cap = cv2.VideoCapture(str(video_path))
    ok, frame = cap.read()
    cap.release()
    return frame if ok else None


def luu_khung_hinh(file_storage, dich):
    """Ảnh -> lưu jpg. Video -> lấy khung đầu. Ném ValueError nếu không đọc được."""
    ext = Path(file_storage.filename or "").suffix.lower()
    dich = Path(dich)
    if ext in ANH_EXT:
        import numpy as np
        buf = np.frombuffer(file_storage.read(), dtype="uint8")
        img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    elif ext in VIDEO_EXT:
        tam = dich.with_suffix(".tmp" + ext)
        file_storage.save(tam)
        try:
            img = lay_khung_dau(tam)
        finally:
            tam.unlink(missing_ok=True)
    else:
        raise ValueError("Chỉ nhận ảnh (jpg, png) hoặc video (mp4, avi, mov, mkv)")
    if img is None:
        raise ValueError("Không đọc được file")
    cv2.imwrite(str(dich), img)


# ---------- chạy video ----------
def bat_dau(file_storage, ma_o, vung_ti_le, data_dir, luu_su_kien):
    ten = Path(file_storage.filename).name
    if Path(ten).suffix.lower() not in VIDEO_EXT:
        ten += ".mp4"
    job = uuid.uuid4().hex[:8]
    duong_dan = Path(data_dir) / "videos" / f"{job}_{ten}"
    file_storage.save(duong_dan)
    with _LOCK:
        _JOBS[job] = {"trang_thai": "dang_chay", "tien_do": 0.0, "su_kien": [], "loi": None,
                      "che_do": che_do(), "ten": ten}
    threading.Thread(target=_chay, args=(job, duong_dan, ma_o, vung_ti_le, data_dir, luu_su_kien),
                     daemon=True).start()
    return job


def trang_thai(job):
    with _LOCK:
        j = _JOBS.get(job)
        return dict(j, su_kien=list(j["su_kien"])) if j else None


def _chay(job, path, ma_o, vung_ti_le, data_dir, luu_su_kien):
    def cap_nhat(**kw):
        with _LOCK:
            _JOBS[job].update(kw)

    def on_event(ev):
        kq, ma = luu_su_kien(ev)
        if ma >= 400:
            raise ValueError("; ".join(kq["loi"]))
        with _LOCK:
            _JOBS[job]["su_kien"].append(kq["id"])

    try:
        cap = cv2.VideoCapture(str(path))
        rong, cao = int(cap.get(3)), int(cap.get(4))
        cap.release()
        if not rong or not cao:
            raise ValueError("Không đọc được video")
        vung_px = vung_mod.sang_pixel(vung_ti_le, rong, cao)
        pl = _pipeline_that()
        if pl:
            pl.chay_video(str(path), ma_o, vung_px, on_event, lambda t: cap_nhat(tien_do=t))
        else:
            _mock(path, ma_o, vung_px, data_dir, on_event, lambda t: cap_nhat(tien_do=t))
        cap_nhat(trang_thai="xong", tien_do=1.0)
    except Exception as e:  # lỗi pipeline hiện ra trên trang, không làm sập webapp
        cap_nhat(trang_thai="loi", loi=f"{type(e).__name__}: {e}")


# ---------- BẢN GIẢ ----------
MAU = [  # (từ khoá trong tên file, loai, muc, du_lieu)
    ("dem", "dem_thieu", "canh_bao", {"dem": 22, "dang_ky": 25}),
    ("nguoi", "nguoi_la", "canh_bao", {"khung": 12}),
    ("lac", "lac_chuong", "khan_cap", {"id_theo_doi": 7, "giay_ngoai": 6}),
    ("ngu", "tho_nhanh", "canh_bao", {"nhip": 48, "gio_nam": 4}),
    ("an", "bo_an", "canh_bao", {"diem_nghi_van": 0.7}),
]


def _mock(path, ma_o, vung_px, data_dir, on_event, tien_do):
    ten = Path(path).name.lower()
    chon = [m for m in MAU if m[0] in ten] or random.sample(MAU, 2)
    khung = lay_khung_dau(path)
    for i, (_, loai, muc, dl) in enumerate(chon):
        time.sleep(1.2)
        anh = None
        if khung is not None and loai in ("lac_chuong", "dem_thieu", "nguoi_la"):
            h, w = khung.shape[:2]
            x, y = random.randint(w // 6, w // 2), random.randint(h // 6, h // 2)
            img = khung.copy()
            cv2.rectangle(img, (x, y), (x + w // 5, y + h // 5), (0, 0, 255), 4)
            anh = f"recordings/su_kien/mock_{int(time.time()*1000)}_{i}.jpg"
            cv2.imwrite(str(Path(data_dir) / anh), img)
        on_event({"loai": loai, "o": ma_o, "muc": muc, "anh": anh, "du_lieu": {**dl, "mock": True},
                  "thoi_gian": datetime.now().replace(microsecond=0).isoformat()})
        tien_do((i + 1) / len(chon))
