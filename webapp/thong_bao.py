"""Lớp thông báo: nhận sự kiện, quyết định hiện ngay (banner) hay chỉ lưu.

Quy tắc (sửa ở đây nếu nhóm đổi ý):
  1. nghi_trom, lac_chuong, nghi_chet          -> luôn hiện ngay.
  2. muc == khan_cap                           -> hiện ngay.
  3. nguoi_la                                  -> chỉ hiện khi đang trong giờ canh gác
                                                  và canh gác đang bật; ngoài giờ chỉ lưu.
  4. muc == canh_bao                           -> hiện ngay.
  5. muc == thong_tin (vd dem_du)              -> chỉ lưu, xem trong trang Sự kiện.
"""
from datetime import datetime

import events


def _phut(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def trong_gio_canh_gac(settings, thoi_gian):
    cg = settings["gio_canh_gac"]
    if not cg.get("bat"):
        return False
    t = datetime.fromisoformat(thoi_gian)
    now = t.hour * 60 + t.minute
    tu, den = _phut(cg["tu"]), _phut(cg["den"])
    if tu <= den:
        return tu <= now < den
    return now >= tu or now < den  # qua nửa đêm, vd 20:00–05:00


def quyet_dinh(ev, settings):
    """Trả về True nếu phải hiện banner ngay."""
    if ev["loai"] in events.LUON_HIEN_NGAY or ev["muc"] == "khan_cap":
        return True
    if ev["loai"] == "nguoi_la":
        return trong_gio_canh_gac(settings, ev["thoi_gian"])
    return ev["muc"] == "canh_bao"


# ---------- kiểm tra cài đặt ----------
def _hhmm_ok(s):
    try:
        datetime.strptime(s, "%H:%M")
        return True
    except (TypeError, ValueError):
        return False


def _tinh_den(tu, phut):
    m = (_phut(tu) + phut) % (24 * 60)
    return f"{m // 60:02d}:{m % 60:02d}"


def kiem_tra_cai_dat(data):
    """Trả về (cai_dat_chuan_hoa, loi). Chỉ nhận các khoá đã biết."""
    loi, out = [], {}
    if "gio_canh_gac" in data:
        g = data["gio_canh_gac"] if isinstance(data["gio_canh_gac"], dict) else {}
        if not (_hhmm_ok(g.get("tu")) and _hhmm_ok(g.get("den"))):
            loi.append("Giờ canh gác phải dạng HH:MM")
        else:
            out["gio_canh_gac"] = {"bat": bool(g.get("bat")), "tu": g["tu"], "den": g["den"]}
    if "gio_dem" in data:
        g = data["gio_dem"] if isinstance(data["gio_dem"], dict) else {}
        tu, den = g.get("tu"), g.get("den")
        try:
            phut = int(g.get("phut")) if g.get("phut") is not None else None
        except (TypeError, ValueError):
            phut = 0
        if not _hhmm_ok(tu):
            loi.append("Giờ đếm: giờ bắt đầu phải dạng HH:MM")
        elif den and _hhmm_ok(den):
            kc = (_phut(den) - _phut(tu)) % (24 * 60) or 15
            out["gio_dem"] = {
                "bat": bool(g.get("bat", True)),
                "tu": tu,
                "den": den,
                "phut": phut if (phut and 1 <= phut <= 240) else min(max(kc, 1), 240),
            }
        elif phut is not None and 1 <= phut <= 240:
            out["gio_dem"] = {
                "bat": bool(g.get("bat", True)),
                "tu": tu,
                "den": _tinh_den(tu, phut),
                "phut": phut,
            }
        else:
            loi.append("Giờ đếm: cần khoảng giờ hợp lệ hoặc thời lượng 1–240 phút")
    if "gio_cho_an" in data:
        ds = data["gio_cho_an"]
        if not isinstance(ds, list) or not ds or not all(_hhmm_ok(x) for x in ds):
            loi.append("Giờ cho ăn phải là danh sách HH:MM")
        else:
            out["gio_cho_an"] = sorted(ds)
    if "tu_dong" in data:
        td = data["tu_dong"] if isinstance(data["tu_dong"], dict) else {}
        td_out = {}
        for k in ("dem_lon", "canh_gac", "phat_trien", "an_uong", "lac_chuong", "suc_khoe"):
            if k in td:
                td_out[k] = bool(td[k])
        for k in ("phat_trien_tu", "phat_trien_den", "lac_chuong_tu", "lac_chuong_den", "suc_khoe_tu", "suc_khoe_den"):
            if k in td:
                if _hhmm_ok(td[k]):
                    td_out[k] = td[k]
                else:
                    loi.append(f"Khung giờ '{k}' phải dạng HH:MM")
        if "phut_an" in td:
            try:
                pa = int(td["phut_an"])
                if 5 <= pa <= 180:
                    td_out["phut_an"] = pa
                else:
                    loi.append("Thời gian theo dõi bữa ăn phải từ 5–180 phút")
            except (TypeError, ValueError):
                loi.append("Thời gian theo dõi bữa ăn phải là số phút")
        out["tu_dong"] = td_out
    if "nguong" in data:
        ng, ok = data["nguong"], {}
        for k, v in ng.items():
            try:
                v = float(v)
            except (TypeError, ValueError):
                loi.append(f"Ngưỡng '{k}' phải là số"); continue
            if v <= 0:
                loi.append(f"Ngưỡng '{k}' phải > 0"); continue
            ok[k] = int(v) if v == int(v) else v
        out["nguong"] = ok
    return out, loi
