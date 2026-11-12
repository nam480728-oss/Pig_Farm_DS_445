"""Định dạng sự kiện thống nhất (mục 8) – TV2, TV4, TV5 gửi, TV3 nhận.

Chốt tuần 1; đổi gì phải báo cả nhóm.
"""
from datetime import datetime

LOAI = {
    "dem_thieu":  "Đếm thiếu",
    "dem_du":     "Đếm đủ",
    "nguoi_la":   "Người lạ",
    "nghi_trom":  "Nghi trộm",
    "lac_chuong": "Lợn sổng chuồng",
    "nghi_chet":  "Nghi chết",
    "tho_nhanh":  "Thở nhanh",
    "bo_an":      "Bỏ ăn",
    "o_an_kem":   "Ô ăn kém",
}
MUC = {"khan_cap": "Khẩn cấp", "canh_bao": "Cảnh báo", "thong_tin": "Thông tin"}

# Luôn hiện ngay, bất kể giờ (theo phân công)
LUON_HIEN_NGAY = {"nghi_trom", "lac_chuong", "nghi_chet"}

REQUIRED = ("loai", "o", "thoi_gian", "muc")


def validate(payload):
    """Trả về (su_kien_chuan_hoa, danh_sach_loi)."""
    errs = []
    if not isinstance(payload, dict):
        return None, ["Body phải là JSON object"]
    for k in REQUIRED:
        if not payload.get(k):
            errs.append(f"Thiếu trường '{k}'")
    if errs:
        return None, errs
    if payload["loai"] not in LOAI:
        errs.append(f"loai '{payload['loai']}' không hợp lệ; chấp nhận: {', '.join(LOAI)}")
    if payload["muc"] not in MUC:
        errs.append(f"muc '{payload['muc']}' không hợp lệ; chấp nhận: {', '.join(MUC)}")
    try:
        datetime.fromisoformat(payload["thoi_gian"])
    except (TypeError, ValueError):
        errs.append("thoi_gian phải dạng ISO, vd 2026-11-10T02:14:00")
    du_lieu = payload.get("du_lieu") or {}
    if not isinstance(du_lieu, dict):
        errs.append("du_lieu phải là object")
    if errs:
        return None, errs
    return {
        "loai": payload["loai"],
        "o": str(payload["o"]),
        "thoi_gian": payload["thoi_gian"],
        "muc": payload["muc"],
        "anh": payload.get("anh"),
        "du_lieu": du_lieu,
    }, []
