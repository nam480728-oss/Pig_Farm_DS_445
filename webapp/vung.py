"""Vùng vẽ trên ảnh camera của mỗi ô: lưu, kiểm tra, đổi sang pixel.

Toạ độ lưu theo tỉ lệ 0–1 (x / chiều rộng, y / chiều cao) nên dùng được với mọi độ phân giải
video. Khi dùng trong pipeline: `sang_pixel(vung, rong, cao)` hoặc tự nhân x*rong, y*cao.

Cấu trúc (khoá nào chưa vẽ thì không có):
{
  "o":          [[x,y], ...],            # đa giác ô chuồng, >= 3 điểm
  "mang_an":    [ [[x,y], ...], ... ],   # danh sách đa giác máng ăn
  "lac_chuong": {"kieu": "vung", "diem": [[x,y], ...]}                 # vùng NGOÀI ô
             hoặc {"kieu": "vach", "diem": [[x,y],[x,y]], "diem_ngoai": [x,y]}  # vạch mức;
                                       # diem_ngoai = một điểm nằm ở phía ngoài vạch
  "vat_tham_chieu": {"diem": [[x,y],[x,y]], "cm": 50.0}   # đoạn thẳng có độ dài thật (cm)
}
"""
import json

KHOA = ("o", "mang_an", "lac_chuong", "vat_tham_chieu")


def _diem(p):
    return (isinstance(p, (list, tuple)) and len(p) == 2
            and all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in p))


def _da_giac(ds):
    return isinstance(ds, list) and len(ds) >= 3 and all(_diem(p) for p in ds)


def kiem_tra(v):
    """Trả về (vung_chuan_hoa, loi)."""
    loi, out = [], {}
    if not isinstance(v, dict):
        return None, ["Vùng phải là object"]
    for k in v:
        if k not in KHOA:
            loi.append(f"Khoá lạ '{k}'")
    if v.get("o") is not None:
        if _da_giac(v["o"]): out["o"] = v["o"]
        else: loi.append("Ô chuồng: cần ≥ 3 điểm, toạ độ trong 0–1")
    if v.get("mang_an") is not None:
        ds = v["mang_an"]
        if isinstance(ds, list) and all(_da_giac(d) for d in ds): out["mang_an"] = ds
        else: loi.append("Máng ăn: mỗi máng cần ≥ 3 điểm")
    lc = v.get("lac_chuong")
    if lc is not None:
        if lc.get("kieu") == "vung" and _da_giac(lc.get("diem")):
            out["lac_chuong"] = {"kieu": "vung", "diem": lc["diem"]}
        elif (lc.get("kieu") == "vach" and isinstance(lc.get("diem"), list) and len(lc["diem"]) == 2
              and all(_diem(p) for p in lc["diem"]) and _diem(lc.get("diem_ngoai"))):
            out["lac_chuong"] = {"kieu": "vach", "diem": lc["diem"], "diem_ngoai": lc["diem_ngoai"]}
        else:
            loi.append("Lạc chuồng: 'vung' cần ≥ 3 điểm; 'vach' cần 2 điểm + diem_ngoai")
    vt = v.get("vat_tham_chieu")
    if vt is not None:
        d = vt.get("diem")
        cm = vt.get("cm")
        if (isinstance(d, list) and len(d) == 2 and all(_diem(p) for p in d)
                and isinstance(cm, (int, float)) and cm > 0):
            out["vat_tham_chieu"] = {"diem": d, "cm": float(cm)}
        else:
            loi.append("Vật tham chiếu: 2 điểm và độ dài cm > 0")
    return (out, loi) if not loi else (None, loi)


def doc(conn, ma):
    r = conn.execute("SELECT vung_json FROM o_chuong WHERE ma=?", (ma,)).fetchone()
    if r is None:
        return None
    return json.loads(r["vung_json"]) if r["vung_json"] else {}


def luu(conn, ma, vung):
    conn.execute("UPDATE o_chuong SET vung_json=? WHERE ma=?",
                 (json.dumps(vung, ensure_ascii=False), ma))


def sang_pixel(vung, rong, cao):
    """Đổi toàn bộ toạ độ 0–1 sang pixel (làm tròn). Dùng cho PolygonZone của Supervision."""
    def p(pt): return [round(pt[0] * rong), round(pt[1] * cao)]
    out = {}
    if "o" in vung: out["o"] = [p(x) for x in vung["o"]]
    if "mang_an" in vung: out["mang_an"] = [[p(x) for x in d] for d in vung["mang_an"]]
    if "lac_chuong" in vung:
        lc = vung["lac_chuong"]
        out["lac_chuong"] = {**lc, "diem": [p(x) for x in lc["diem"]]}
        if "diem_ngoai" in lc: out["lac_chuong"]["diem_ngoai"] = p(lc["diem_ngoai"])
    if "vat_tham_chieu" in vung:
        vt = vung["vat_tham_chieu"]
        out["vat_tham_chieu"] = {"diem": [p(x) for x in vt["diem"]], "cm": vt["cm"]}
        (x1, y1), (x2, y2) = out["vat_tham_chieu"]["diem"]
        dai_px = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        out["vat_tham_chieu"]["cm_moi_pixel"] = round(vt["cm"] / dai_px, 4) if dai_px else None
    return out
