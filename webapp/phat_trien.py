"""Báo cáo phát triển của một đàn: trung bình, tăng cân, độ đồng đều, con còi, con lớn nhanh.

Dữ liệu vào: bảng lan_do (mỗi lần đo một con: con_id, thoi_gian, kg, anh).
  - Webapp tự tính báo cáo từ lan_do. Module phát triển của TV2 chỉ cần ghi lan_do
    (POST /api/lan-do), hoặc có thể thay hàm bao_cao() này nếu muốn tính khác.

Định nghĩa (đổi ở đây nếu nhóm thống nhất khác):
  - Mốc (kg)     = kg_nhap_tb + moc_kg_ngay × số ngày tuổi kể từ ngày nhập  (cột của bảng dan).
  - Trung bình   = trung bình kg các con ở NGÀY ĐO GẦN NHẤT.
  - Tăng kg, %   = so với ngày đo liền trước, chỉ tính các con có mặt ở cả hai ngày.
  - Đồng đều     = % số con có kg trong ±10% trung bình đàn (chuẩn chăn nuôi), kèm CV% = độ lệch chuẩn / TB.
  - Con còi      = kg ≤ TB × (1 − coi_phan_tram/100).
  - Con lớn nhanh = kg ≥ TB × (1 + lon_nhanh_phan_tram/100).
  - chenh_moc    = kg − mốc;  chenh_tb = kg − trung bình đàn.
"""
from datetime import date, datetime
from statistics import mean, pstdev

import db

DONG_DEU_BIEN = 0.10


def _ngay(s):
    return datetime.fromisoformat(s).date()


def _con(r, tb, moc):
    return {"con_id": r["con_id"], "anh": r["anh"], "kg": round(r["kg"], 1),
            "chenh_moc": round(r["kg"] - moc, 1), "chenh_tb": round(r["kg"] - tb, 1),
            "chenh_tb_pct": round((r["kg"] - tb) / tb * 100, 1)}


def bao_cao(conn, ma):
    """Trả về dict báo cáo, hoặc None nếu không có đàn; có đàn nhưng chưa có lần đo thì 'co_du_lieu': False."""
    d = conn.execute("SELECT * FROM dan WHERE ma=?", (ma,)).fetchone()
    if not d:
        return None
    st = db.get_settings(conn)["nguong"]
    rows = conn.execute("SELECT * FROM lan_do WHERE dan=? ORDER BY thoi_gian", (ma,)).fetchall()
    out = {"dan": ma, "o": d["o"], "so_con": d["so_con"], "co_du_lieu": bool(rows)}
    if not rows:
        return out

    theo_ngay = {}
    for r in rows:
        theo_ngay.setdefault(r["thoi_gian"][:10], {})[r["con_id"]] = r   # 1 con 1 ngày: lấy lần đo cuối
    ngays = sorted(theo_ngay)
    gan = theo_ngay[ngays[-1]]
    tb = mean(r["kg"] for r in gan.values())

    def moc_tai(ngay):
        return d["kg_nhap_tb"] + d["moc_kg_ngay"] * (_ngay(ngay) - _ngay(d["ngay_nhap"])).days

    moc = moc_tai(ngays[-1])
    out.update(
        ngay_do=ngays[-1], so_con_do=len(gan),
        tuoi_ngay=(_ngay(ngays[-1]) - _ngay(d["ngay_nhap"])).days,
        tb_kg=round(tb, 1), moc_kg=round(moc, 1), tb_chenh_moc=round(tb - moc, 1),
        cv_pct=round(pstdev([r["kg"] for r in gan.values()]) / tb * 100, 1) if len(gan) > 1 else 0.0,
        dong_deu_pct=round(100 * sum(abs(r["kg"] - tb) <= DONG_DEU_BIEN * tb for r in gan.values()) / len(gan), 1),
        tb_kg_ky_truoc=None, tang_kg=None, tang_pct=None, tang_kg_ngay=None, ngay_ky_truoc=None)

    if len(ngays) >= 2:
        truoc = theo_ngay[ngays[-2]]
        chung = [c for c in gan if c in truoc]
        if chung:
            a, b = mean(truoc[c]["kg"] for c in chung), mean(gan[c]["kg"] for c in chung)
            so_ngay = (_ngay(ngays[-1]) - _ngay(ngays[-2])).days or 1
            out.update(ngay_ky_truoc=ngays[-2], tb_kg_ky_truoc=round(a, 1), tang_kg=round(b - a, 1),
                       tang_pct=round((b - a) / a * 100, 1), tang_kg_ngay=round((b - a) / so_ngay, 2))

    coi = sorted((r for r in gan.values() if r["kg"] <= tb * (1 - st["coi_phan_tram"] / 100)),
                 key=lambda r: r["kg"])
    lon = sorted((r for r in gan.values() if r["kg"] >= tb * (1 + st["lon_nhanh_phan_tram"] / 100)),
                 key=lambda r: -r["kg"])
    out["con_coi"] = [_con(r, tb, moc) for r in coi]
    out["con_lon_nhanh"] = [_con(r, tb, moc) for r in lon]
    out["chuoi"] = [{"ngay": n, "tb": round(mean(r["kg"] for r in theo_ngay[n].values()), 1),
                     "moc": round(moc_tai(n), 1)} for n in ngays]
    return out


def ve_bieu_do(chuoi, rong=340, cao=165):
    """SVG đường: trung bình đàn (xanh) và mốc (nét đứt). Trả về chuỗi SVG."""
    if len(chuoi) < 2:
        return ""
    gia_tri = [x["tb"] for x in chuoi] + [x["moc"] for x in chuoi]
    lo, hi = min(gia_tri) * 0.94, max(gia_tri) * 1.06
    if hi <= lo:
        hi = lo + 1
    le_trai, le_phai, le_tren, le_duoi = 32, 12, 16, 26
    w_ve = rong - le_trai - le_phai
    h_ve = cao - le_tren - le_duoi

    def toa_do(i, v):
        x = le_trai + i * w_ve / (len(chuoi) - 1)
        y = cao - le_duoi - (v - lo) / (hi - lo) * h_ve
        return (x, y)

    def duong(khoa):
        return " ".join("%.1f,%.1f" % toa_do(i, x[khoa]) for i, x in enumerate(chuoi))

    pts_tb = [toa_do(i, x["tb"]) for i, x in enumerate(chuoi)]
    pts_moc = [toa_do(i, x["moc"]) for i, x in enumerate(chuoi)]
    vung_tb = (
        f"M {pts_tb[0][0]:.1f},{cao - le_duoi} "
        + " ".join(f"L {x:.1f},{y:.1f}" for x, y in pts_tb)
        + f" L {pts_tb[-1][0]:.1f},{cao - le_duoi} Z"
    )

    luoi_y = ""
    for f in (0.0, 0.5, 1.0):
        y = le_tren + f * h_ve
        val = round(hi - f * (hi - lo))
        luoi_y += (
            f'<line x1="{le_trai}" y1="{y:.1f}" x2="{rong - le_phai}" y2="{y:.1f}" '
            f'stroke="currentColor" stroke-opacity="0.08" stroke-dasharray="3 3"/>'
            f'<text x="{le_trai - 6}" y="{y + 3:.1f}" font-size="10" text-anchor="end" '
            f'fill="currentColor" opacity=".55">{val}</text>'
        )

    nhan = "".join(
        '<text x="%.1f" y="%d" font-size="10" text-anchor="%s" fill="currentColor" opacity=".6">%s</text>'
        % (
            toa_do(i, lo)[0],
            cao - 6,
            "start" if i == 0 else ("end" if i == len(chuoi) - 1 else "middle"),
            x["ngay"][5:].replace("-", "/"),
        )
        for i, x in enumerate(chuoi)
    )

    cham_moc = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="var(--panel)" stroke="#94a3b8" stroke-width="1.5"/>'
        for x, y in pts_moc
    )
    cham_tb = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="var(--brand)" stroke="var(--panel)" stroke-width="1.5"/>'
        for x, y in pts_tb
    )

    return (
        f'<svg viewBox="0 0 {rong} {cao}" role="img" aria-label="Trung bình đàn so với mốc" width="100%">'
        f'<defs><linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="var(--brand)" stop-opacity="0.26"/>'
        f'<stop offset="100%" stop-color="var(--brand)" stop-opacity="0.0"/>'
        f'</linearGradient></defs>'
        f'{luoi_y}'
        f'<path d="{vung_tb}" fill="url(#chartGrad)"/>'
        f'<polyline points="{duong("moc")}" fill="none" stroke="#94a3b8" stroke-width="2" stroke-dasharray="5 4" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<polyline points="{duong("tb")}" fill="none" stroke="var(--brand)" stroke-width="2.75" stroke-linecap="round" stroke-linejoin="round"/>'
        f'{cham_moc}{cham_tb}{nhan}</svg>'
    )
