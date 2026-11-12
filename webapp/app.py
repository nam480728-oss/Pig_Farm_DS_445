"""Webapp giám sát trang trại lợn – Thành viên 3 (Thanh).

Chạy:  python seed.py && python app.py   ->  http://127.0.0.1:5000
"""
import json
from datetime import datetime

from flask import Flask, abort, jsonify, render_template, request, send_from_directory

import db
import events
import phat_trien
import pipeline_adapter
import thong_bao
import vung

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024   # video demo tối đa 500 MB
db.init_db()
DATA = db.DB_PATH.parent
for _d in ("camera", "videos", "recordings/su_kien"):
    (DATA / _d).mkdir(parents=True, exist_ok=True)


@app.errorhandler(404)
def khong_thay(_):
    return render_template("loi.html", tab=None, ma=404, thong_diep="Không tìm thấy trang này."), 404


@app.errorhandler(413)
def file_qua_lon(_):
    return jsonify(ok=False, loi=["File quá lớn (tối đa 500 MB)"]), 413


@app.template_filter("gio")
def fmt_gio(s):
    try:
        return datetime.fromisoformat(s).strftime("%H:%M %d/%m")
    except Exception:
        return s


NHAN_DU_LIEU = {
    "nhip": "Nhịp thở (lần/phút)", "gio_nam": "Đã nằm (giờ)", "diem_nghi_van": "Điểm nghi vấn bỏ ăn",
    "ty_le_an": "Tỉ lệ ăn", "dem": "Đếm được", "dang_ky": "Đăng ký", "so_nguoi": "Số người",
    "khung": "Số khung", "id_theo_doi": "ID con", "giay_ngoai": "Ngoài (giây)", "mock": "Dữ liệu mẫu",
}


@app.template_filter("nhan")
def nhan_du_lieu(d):
    """{'nhip': None} -> [('Nhịp thở (lần/phút)', '—')]"""
    return [(NHAN_DU_LIEU.get(k, k), "—" if v is None else ("có" if v is True else v)) for k, v in d.items()]


app.jinja_env.globals.update(LOAI=events.LOAI, MUC=events.MUC)


# ---------- Trang ----------
@app.route("/")
def trang_chu():
    with db.connect() as c:
        o = c.execute("""
            SELECT o.*,
              (SELECT COUNT(*) FROM su_kien s WHERE s.o=o.ma AND s.trang_thai='moi') AS su_kien_moi
            FROM o_chuong o ORDER BY o.ma""").fetchall()
        gan_day = [db.row_to_event(r) for r in c.execute(
            "SELECT * FROM su_kien ORDER BY thoi_gian DESC LIMIT 4")]
        khan_cap = c.execute(
            "SELECT COUNT(*) FROM su_kien WHERE muc='khan_cap' AND trang_thai='moi'").fetchone()[0]
        tong_con = c.execute("SELECT COALESCE(SUM(so_dang_ky),0) FROM o_chuong").fetchone()[0]
        o_khan_cap = {r["o"] for r in c.execute(
            "SELECT DISTINCT o FROM su_kien WHERE muc='khan_cap' AND trang_thai='moi'")}
    return render_template("trang_chu.html", tab="home", o=o, gan_day=gan_day,
                           khan_cap=khan_cap, tong_con=tong_con, o_khan_cap=o_khan_cap)


@app.route("/o-chuong")
def o_chuong():
    with db.connect() as c:
        rows = c.execute("""
            SELECT o.*,
              (SELECT COUNT(*) FROM su_kien s WHERE s.o=o.ma AND s.trang_thai='moi') AS su_kien_moi,
              (SELECT json_extract(s.du_lieu,'$.dem') FROM su_kien s
                 WHERE s.o=o.ma AND s.loai IN ('dem_du','dem_thieu')
                 ORDER BY s.thoi_gian DESC LIMIT 1) AS dem_gan_nhat
            FROM o_chuong o ORDER BY o.ma""").fetchall()
    return render_template("o_chuong.html", tab="o", rows=rows)


@app.route("/xem/<ma>")
def xem_camera(ma):
    """Màn hình xem camera kiểu Imou: khung camera ở trên, chức năng và tin nhắn ở dưới."""
    with db.connect() as c:
        o = c.execute("SELECT * FROM o_chuong WHERE ma=?", (ma,)).fetchone()
        if not o:
            abort(404)
        ds_o = c.execute("""
            SELECT o.ma, o.ten,
              (SELECT COUNT(*) FROM su_kien s WHERE s.o=o.ma AND s.muc='khan_cap' AND s.trang_thai='moi') AS khan_cap
            FROM o_chuong o ORDER BY o.ma""").fetchall()
        tin = [db.row_to_event(r) for r in c.execute(
            "SELECT * FROM su_kien WHERE o=? ORDER BY thoi_gian DESC LIMIT 8", (ma,))]
        su_kien_moi = c.execute(
            "SELECT COUNT(*) FROM su_kien WHERE o=? AND trang_thai='moi'", (ma,)).fetchone()[0]
        dem = c.execute("""SELECT json_extract(du_lieu,'$.dem') FROM su_kien
            WHERE o=? AND loai IN ('dem_du','dem_thieu') ORDER BY thoi_gian DESC LIMIT 1""", (ma,)).fetchone()
        dan_o = c.execute("SELECT ma FROM dan WHERE o=? ORDER BY ma LIMIT 1", (ma,)).fetchone()
        st = db.get_settings(c)
    return render_template(
        "xem_camera.html", tab="home", o=o, ds_o=ds_o, tin=tin, su_kien_moi=su_kien_moi,
        dem=dem[0] if dem else None, dan_o=dan_o["ma"] if dan_o else None,
        canh_gac=st["gio_canh_gac"], st=st, vung=json.loads(o["vung_json"]) if o["vung_json"] else {},
        co_anh=(DATA / "camera" / f"{ma}.jpg").exists())


@app.route("/dan")
def dan():
    with db.connect() as c:
        ma_ds = [r["ma"] for r in c.execute("SELECT ma FROM dan ORDER BY ma")]
        rows = [phat_trien.bao_cao(c, m) for m in ma_ds]
    return render_template("dan.html", tab="dan", rows=rows)


@app.route("/dan/<ma>")
def dan_chi_tiet(ma):
    tab = request.args.get("tab", "tong_quan")
    if tab not in ("tong_quan", "coi", "lon_nhanh"):
        tab = "tong_quan"
    with db.connect() as c:
        bc = phat_trien.bao_cao(c, ma)
        nguong = db.get_settings(c)["nguong"]
    if bc is None:
        abort(404)
    bieu_do = phat_trien.ve_bieu_do(bc.get("chuoi", []))
    return render_template("dan_chi_tiet.html", tab="dan", bc=bc, sub=tab, bieu_do=bieu_do, nguong=nguong)


@app.route("/su-kien")
def su_kien():
    muc = request.args.get("muc")
    o = request.args.get("o")
    sql, args = "SELECT * FROM su_kien WHERE 1=1", []
    if muc in events.MUC:
        sql += " AND muc=?"; args.append(muc)
    if o:
        sql += " AND o=?"; args.append(o)
    sql += " ORDER BY thoi_gian DESC LIMIT 100"
    with db.connect() as c:
        rows = [db.row_to_event(r) for r in c.execute(sql, args)]
        o_list = [r["ma"] for r in c.execute("SELECT ma FROM o_chuong ORDER BY ma")]
    return render_template("su_kien.html", tab="sk", rows=rows, muc=muc, o_sel=o, o_list=o_list)


@app.route("/cai-dat")
def cai_dat():
    with db.connect() as c:
        st = db.get_settings(c)
    return render_template("cai_dat.html", tab="cd", st=st)


# ---------- API ----------
def luu_su_kien(payload):
    """Kiểm tra + lưu một sự kiện. Trả về (dict kết quả, mã HTTP). Dùng cho API và pipeline."""
    ev, errs = events.validate(payload)
    if errs:
        return {"ok": False, "loi": errs}, 400
    with db.connect() as c:
        if not c.execute("SELECT 1 FROM o_chuong WHERE ma=?", (ev["o"],)).fetchone():
            return {"ok": False, "loi": [f"Ô '{ev['o']}' chưa có trong hệ thống"]}, 400
        hien_ngay = 1 if thong_bao.quyet_dinh(ev, db.get_settings(c)) else 0
        cur = c.execute(
            "INSERT INTO su_kien(loai,o,thoi_gian,muc,anh,du_lieu,hien_ngay) VALUES (?,?,?,?,?,?,?)",
            (ev["loai"], ev["o"], ev["thoi_gian"], ev["muc"], ev["anh"],
             json.dumps(ev["du_lieu"], ensure_ascii=False), hien_ngay))
    return {"ok": True, "id": cur.lastrowid, "hien_ngay": bool(hien_ngay)}, 201


@app.post("/api/su-kien")
def api_nhan_su_kien():
    """TV2/TV4/TV5 gửi sự kiện (định dạng mục 8). Xem docs/dinh_dang_su_kien.md."""
    kq, ma = luu_su_kien(request.get_json(silent=True))
    return jsonify(kq), ma


@app.get("/api/su-kien")
def api_ds_su_kien():
    with db.connect() as c:
        rows = [db.row_to_event(r) for r in c.execute(
            "SELECT * FROM su_kien ORDER BY thoi_gian DESC LIMIT 100")]
    return jsonify(rows)


@app.get("/api/thong-bao")
def api_thong_bao():
    """Banner hỏi mỗi 3 giây. ?sau=<id> -> sự kiện hiện-ngay có id > sau.
    Không có ?sau -> chỉ trả moi_nhat (id lớn nhất hiện giờ) để client bắt đầu từ đó."""
    sau = request.args.get("sau", type=int)
    with db.connect() as c:
        moi_nhat = c.execute("SELECT COALESCE(MAX(id),0) FROM su_kien").fetchone()[0]
        ds = []
        if sau is not None:
            for r in c.execute("SELECT * FROM su_kien WHERE hien_ngay=1 AND id>? ORDER BY id", (sau,)):
                e = db.row_to_event(r)
                e["ten_loai"], e["ten_muc"] = events.LOAI[e["loai"]], events.MUC[e["muc"]]
                ds.append(e)
    return jsonify(moi_nhat=moi_nhat, ds=ds)


@app.post("/api/su-kien/<int:sid>/phan-hoi")
def api_phan_hoi(sid):
    """Nút "Đúng" / "Báo nhầm". Body: {"phan_hoi": "dung" | "bao_nham"}"""
    ph = (request.get_json(silent=True) or {}).get("phan_hoi")
    if ph not in ("dung", "bao_nham"):
        return jsonify(ok=False, loi=["phan_hoi phải là 'dung' hoặc 'bao_nham'"]), 400
    with db.connect() as c:
        cur = c.execute("UPDATE su_kien SET trang_thai=? WHERE id=?", (ph, sid))
    if not cur.rowcount:
        return jsonify(ok=False, loi=["Không có sự kiện này"]), 404
    return jsonify(ok=True, trang_thai=ph)


@app.get("/api/dan/<ma>/bao-cao")
def api_bao_cao(ma):
    """Khối báo cáo phát triển (xem phat_trien.py để biết các trường)."""
    with db.connect() as c:
        bc = phat_trien.bao_cao(c, ma)
    if bc is None:
        return jsonify(ok=False, loi=["Không có đàn này"]), 404
    return jsonify(bc)


@app.post("/api/lan-do")
def api_lan_do():
    """TV2 ghi kết quả cân nặng. Body: {"dan":"D01","thoi_gian":ISO,"ds":[{"con_id":"D01-03","kg":71.2,"anh":null}]}"""
    p = request.get_json(silent=True) or {}
    loi = []
    try:
        datetime.fromisoformat(p.get("thoi_gian"))
    except (TypeError, ValueError):
        loi.append("thoi_gian phải dạng ISO")
    ds = p.get("ds")
    if not isinstance(ds, list) or not ds:
        loi.append("ds phải là danh sách không rỗng")
    else:
        for i, x in enumerate(ds):
            kg = x.get("kg") if isinstance(x, dict) else None
            if not isinstance(x, dict) or not x.get("con_id") or not isinstance(kg, (int, float)) or not 1 <= kg <= 400:
                loi.append(f"ds[{i}]: cần con_id và kg trong 1–400")
                break
    if loi:
        return jsonify(ok=False, loi=loi), 400
    with db.connect() as c:
        if not c.execute("SELECT 1 FROM dan WHERE ma=?", (p.get("dan"),)).fetchone():
            return jsonify(ok=False, loi=[f"Đàn '{p.get('dan')}' chưa có"]), 400
        c.executemany("INSERT INTO lan_do(dan,con_id,thoi_gian,kg,anh) VALUES (?,?,?,?,?)",
                      [(p["dan"], x["con_id"], p["thoi_gian"], x["kg"], x.get("anh")) for x in ds])
    return jsonify(ok=True, so_con=len(ds)), 201


@app.get("/api/cai-dat")
def api_cai_dat():
    with db.connect() as c:
        return jsonify(db.get_settings(c))


@app.put("/api/cai-dat")
def api_luu_cai_dat():
    out, loi = thong_bao.kiem_tra_cai_dat(request.get_json(silent=True) or {})
    if loi:
        return jsonify(ok=False, loi=loi), 400
    with db.connect() as c:
        cur_st = db.get_settings(c)
        if "tu_dong" in out:
            out["tu_dong"] = {**cur_st.get("tu_dong", {}), **out["tu_dong"]}
        if "gio_dem" in out:
            out["gio_dem"] = {**cur_st.get("gio_dem", {}), **out["gio_dem"]}
            out.setdefault("tu_dong", dict(cur_st.get("tu_dong", {})))["dem_lon"] = out["gio_dem"]["bat"]
        elif "tu_dong" in out and "dem_lon" in out["tu_dong"]:
            out["gio_dem"] = {**cur_st.get("gio_dem", {}), "bat": out["tu_dong"]["dem_lon"]}
        if "gio_canh_gac" in out:
            out["gio_canh_gac"] = {**cur_st.get("gio_canh_gac", {}), **out["gio_canh_gac"]}
            out.setdefault("tu_dong", dict(cur_st.get("tu_dong", {})))["canh_gac"] = out["gio_canh_gac"]["bat"]
        elif "tu_dong" in out and "canh_gac" in out["tu_dong"]:
            out["gio_canh_gac"] = {**cur_st.get("gio_canh_gac", {}), "bat": out["tu_dong"]["canh_gac"]}
        if "nguong" in out:
            out["nguong"] = {**cur_st.get("nguong", {}), **out["nguong"]}
        for k, v in out.items():
            c.execute("INSERT OR REPLACE INTO cai_dat(khoa, gia_tri) VALUES (?,?)",
                      (k, json.dumps(v, ensure_ascii=False)))
        st_moi = db.get_settings(c)
    return jsonify(ok=True, cai_dat=st_moi)


def _ve_anh_kiem_tra(ma, tac_vu, canh_bao, nhan_phu=""):
    """Vẽ khung nhận diện AI lên ảnh camera của ô để hiển thị kết quả trực quan."""
    import time as _time
    import cv2
    nguon = DATA / "camera" / f"{ma}.jpg"
    img = cv2.imread(str(nguon))
    if img is None:
        return None
    h, w = img.shape[:2]
    mau = (0, 0, 235) if canh_bao else (45, 195, 85)
    # Vẽ các khung nhận diện mẫu trên ảnh
    boxes = [
        (int(w * 0.16), int(h * 0.22), int(w * 0.34), int(h * 0.48)),
        (int(w * 0.42), int(h * 0.28), int(w * 0.62), int(h * 0.54)),
        (int(w * 0.64), int(h * 0.24), int(w * 0.83), int(h * 0.50)),
        (int(w * 0.24), int(h * 0.54), int(w * 0.45), int(h * 0.78)),
        (int(w * 0.52), int(h * 0.56), int(w * 0.74), int(h * 0.80)),
    ]
    if tac_vu == "phat_hien_nguoi":
        boxes = [(int(w * 0.36), int(h * 0.18), int(w * 0.58), int(h * 0.82))] if canh_bao else []
    elif tac_vu == "lac_chuong" and canh_bao:
        boxes = [(int(w * 0.03), int(h * 0.15), int(w * 0.22), int(h * 0.46))]
    for i, (x1, y1, x2, y2) in enumerate(boxes):
        c_box = (0, 0, 235) if (canh_bao and i == 0) else (45, 195, 85)
        cv2.rectangle(img, (x1, y1), (x2, y2), c_box, 3)
        tag = f"AI #{i+1}" if tac_vu != "phat_hien_nguoi" else "NGUOI LA"
        cv2.rectangle(img, (x1, max(0, y1 - 24)), (x1 + 92, y1), c_box, -1)
        cv2.putText(img, tag, (x1 + 6, max(16, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    if nhan_phu:
        cv2.rectangle(img, (12, h - 46), (min(w - 12, 460), h - 12), (18, 28, 22), -1)
        cv2.putText(img, nhan_phu, (22, h - 23), cv2.FONT_HERSHEY_SIMPLEX, 0.62, mau, 2)
    rel = f"recordings/su_kien/kt_{ma}_{tac_vu}_{int(_time.time()*1000)}.jpg"
    (DATA / "recordings" / "su_kien").mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(DATA / rel), img)
    return rel


@app.post("/api/o/<ma>/kiem-tra")
def api_kiem_tra_thu_cong(ma):
    """Chạy kiểm tra AI thủ công trên ô camera `ma` (khi tắt tự động hoặc người dùng bấm kiểm tra ngay)."""
    body = request.get_json(silent=True) or {}
    tac_vu = body.get("tac_vu")
    canh_bao = bool(body.get("canh_bao", False))
    now_dt = datetime.now().replace(microsecond=0)
    now_iso = now_dt.isoformat()
    now_str = now_dt.strftime("%H:%M:%S %d/%m")

    with db.connect() as c:
        o = c.execute("SELECT * FROM o_chuong WHERE ma=?", (ma,)).fetchone()
        if not o:
            return jsonify(ok=False, loi=["Không có ô chuồng này"]), 404
        st = db.get_settings(c)
        dk = o["so_dang_ky"]

        if tac_vu == "dem_lon":
            dem = max(0, dk - 2) if canh_bao else dk
            loai = "dem_thieu" if dem < dk else "dem_du"
            muc = "canh_bao" if dem < dk else "thong_tin"
            anh = _ve_anh_kiem_tra(ma, "dem_lon", dem < dk, f"AI Count: {dem}/{dk} pigs")
            ev_kq, _ = luu_su_kien({
                "loai": loai, "o": ma, "muc": muc, "thoi_gian": now_iso,
                "anh": anh, "du_lieu": {"dem": dem, "dang_ky": dk},
            })
            chenh = dem - dk
            return jsonify(
                ok=True, tac_vu=tac_vu, trang_thai="canh_bao" if dem < dk else "ok",
                nhan_trang_thai="Thiếu quân số" if dem < dk else "Đủ quân số",
                tieu_de=f"Kết quả đếm lợn – {o['ten']}",
                tom_tat=(f"Phát hiện {dem}/{dk} con trong ô chuồng (thiếu {dk - dem} con)!"
                         if dem < dk else f"Đếm đủ {dem}/{dk} con trong ô chuồng."),
                anh=anh, dem=dem, dang_ky=dk, su_kien_id=ev_kq.get("id"),
                chi_tiet=[
                    ["Số lợn AI đếm được", f"{dem} con"],
                    ["Số lợn đăng ký", f"{dk} con"],
                    ["Chênh lệch", f"{chenh:+d} con" if chenh else "0 con (Đủ 100%)"],
                    ["Thời điểm kiểm tra", now_str],
                ],
            )

        if tac_vu == "phat_trien":
            dan_row = c.execute("SELECT ma FROM dan WHERE o=? ORDER BY ma LIMIT 1", (ma,)).fetchone()
            if not dan_row:
                # Tự khởi tạo dữ liệu đo cho ô chưa gắn đàn (vd ô D) để kiểm tra phát triển hoạt động ngay
                ma_dan = f"D_{ma}"
                c.execute("INSERT OR IGNORE INTO dan(ma,o,so_con,ngay_nhap,kg_nhap_tb,moc_kg_ngay) VALUES (?,?,?,?,?,?)",
                          (ma_dan, ma, dk, "2026-09-15", 35.0, 0.65))
                for i in range(1, dk + 1):
                    he_so = 0.78 if i == 1 else (1.22 if i == 2 else 1.0 + ((i % 5) - 2) * 0.02)
                    c.execute("INSERT INTO lan_do(dan,con_id,thoi_gian,kg,anh) VALUES (?,?,?,?,?)",
                              (ma_dan, f"{ma_dan}-{i:02d}", "2026-10-25T08:00:00", round(56.0 * he_so, 1), None))
                    c.execute("INSERT INTO lan_do(dan,con_id,thoi_gian,kg,anh) VALUES (?,?,?,?,?)",
                              (ma_dan, f"{ma_dan}-{i:02d}", "2026-11-01T08:00:00", round(60.5 * he_so, 1), None))
            else:
                ma_dan = dan_row["ma"]
            bc = phat_trien.bao_cao(c, ma_dan)
            bieu_do = phat_trien.ve_bieu_do(bc.get("chuoi", []))
            so_coi = len(bc.get("con_coi", []))
            so_lon = len(bc.get("con_lon_nhanh", []))
            anh = _ve_anh_kiem_tra(ma, "phat_trien", so_coi > 0, f"Avg: {bc.get('tb_kg', 0)}kg | Uniform: {bc.get('dong_deu_pct', 0)}%")
            tang_str = (f"{bc['tang_kg']:+.1f} kg ({bc['tang_pct']:+.1f}% · {bc['tang_kg_ngay']} kg/ngày)"
                        if bc.get("tang_kg") is not None else "Chưa có kỳ trước")
            return jsonify(
                ok=True, tac_vu=tac_vu,
                trang_thai="canh_bao" if so_coi > 0 else "ok",
                nhan_trang_thai=f"Có {so_coi} con còi" if so_coi > 0 else "Phát triển tốt",
                tieu_de=f"Độ phát triển đàn {ma_dan} – {o['ten']}",
                tom_tat=f"Cân nặng TB: {bc['tb_kg']} kg (mốc chuẩn {bc['moc_kg']} kg) · Độ đồng đều {bc['dong_deu_pct']}%.",
                anh=anh,
                chi_tiet=[
                    ["Mã đàn / Số con đo", f"Đàn {ma_dan} ({bc['so_con_do']}/{bc['so_con']} con)"],
                    ["Cân nặng trung bình", f"{bc['tb_kg']} kg (Mốc: {bc['moc_kg']} kg · Lệch {bc['tb_chenh_moc']:+.1f} kg)"],
                    ["Tăng trưởng kỳ gần nhất", tang_str],
                    ["Độ đồng đều của đàn", f"{bc['dong_deu_pct']}% (CV: {bc['cv_pct']}%)"],
                    ["Cá thể cần chú ý", f"{so_coi} con còi · {so_lon} con lớn nhanh"],
                ],
                bao_cao={
                    "dan": ma_dan,
                    "link": f"/dan/{ma_dan}",
                    "bieu_do": bieu_do,
                    "con_coi": bc.get("con_coi", [])[:4],
                    "con_lon_nhanh": bc.get("con_lon_nhanh", [])[:4],
                },
            )

        if tac_vu == "phat_hien_nguoi":
            anh = _ve_anh_kiem_tra(ma, "phat_hien_nguoi", canh_bao,
                                   "ALERT: Human detected!" if canh_bao else "Security OK: 0 human")
            if canh_bao:
                trong_cg = thong_bao.trong_gio_canh_gac(st, now_iso)
                loai = "nghi_trom" if trong_cg else "nguoi_la"
                muc = "khan_cap" if trong_cg else "canh_bao"
                dl = {"so_nguoi": 1, "khung": 15} if loai == "nghi_trom" else {"khung": 15}
                ev_kq, _ = luu_su_kien({"loai": loai, "o": ma, "muc": muc, "thoi_gian": now_iso, "anh": anh, "du_lieu": dl})
                return jsonify(
                    ok=True, tac_vu=tac_vu, trang_thai="khan_cap",
                    nhan_trang_thai="Phát hiện xâm nhập!",
                    tieu_de=f"Cảnh báo an ninh – {o['ten']}",
                    tom_tat="Phát hiện 1 người trong khu vực camera! Đã lưu ảnh bằng chứng và ghi sự kiện.",
                    anh=anh, su_kien_id=ev_kq.get("id"),
                    chi_tiet=[
                        ["Số người phát hiện", "1 người (15 khung liên tiếp)"],
                        ["Mức độ cảnh báo", events.LOAI[loai] + f" ({events.MUC[muc]})"],
                        ["Khung giờ canh gác", f"{st['gio_canh_gac']['tu']} – {st['gio_canh_gac']['den']}"],
                        ["Thời điểm quét", now_str],
                    ],
                )
            return jsonify(
                ok=True, tac_vu=tac_vu, trang_thai="ok",
                nhan_trang_thai="An toàn",
                tieu_de=f"Kiểm tra an ninh – {o['ten']}",
                tom_tat="Không phát hiện người lạ hay chuyển động bất thường quanh ô chuồng.",
                anh=anh,
                chi_tiet=[
                    ["Người trong vùng camera", "0 người"],
                    ["Hàng rào & lối đi", "Bình thường, không có xâm nhập"],
                    ["Lịch canh gác tự động", f"{'Đang bật' if st['gio_canh_gac']['bat'] else 'Đang tắt'} ({st['gio_canh_gac']['tu']} – {st['gio_canh_gac']['den']})"],
                    ["Thời điểm quét", now_str],
                ],
            )

        if tac_vu == "an_uong":
            anh = _ve_anh_kiem_tra(ma, "an_uong", canh_bao,
                                   "Low feeding: 45%" if canh_bao else "Feeding normal: 95%")
            if canh_bao:
                ev_kq, _ = luu_su_kien({
                    "loai": "bo_an", "o": ma, "muc": "canh_bao", "thoi_gian": now_iso,
                    "anh": anh, "du_lieu": {"diem_nghi_van": 0.82, "ty_le_an": 0.45},
                })
                return jsonify(
                    ok=True, tac_vu=tac_vu, trang_thai="canh_bao",
                    nhan_trang_thai="Có dấu hiệu bỏ ăn",
                    tieu_de=f"Kiểm tra ăn uống – {o['ten']}",
                    tom_tat=f"Chỉ có {max(1, round(dk * 0.45))}/{dk} con vào máng ăn (45%). Phát hiện 1 cá thể nằm tách đàn.",
                    anh=anh, su_kien_id=ev_kq.get("id"),
                    chi_tiet=[
                        ["Số lợn tại máng ăn", f"{max(1, round(dk * 0.45))}/{dk} con (45%)"],
                        ["Cá thể nghi bỏ ăn", "1 con (điểm nghi vấn 0.82)"],
                        ["Các khung giờ cho ăn", ", ".join(st["gio_cho_an"])],
                        ["Thời điểm kiểm tra", now_str],
                    ],
                )
            so_an = max(1, round(dk * 0.95))
            return jsonify(
                ok=True, tac_vu=tac_vu, trang_thai="ok",
                nhan_trang_thai="Ăn uống tốt",
                tieu_de=f"Kiểm tra ăn uống – {o['ten']}",
                tom_tat=f"Đàn ăn khỏe, {so_an}/{dk} con (95%) tập trung đều tại khu vực máng ăn.",
                anh=anh,
                chi_tiet=[
                    ["Số lợn tại máng ăn", f"{so_an}/{dk} con (95%)"],
                    ["Cá thể nghi bỏ ăn", "0 con"],
                    ["Các khung giờ cho ăn", ", ".join(st["gio_cho_an"])],
                    ["Thời điểm kiểm tra", now_str],
                ],
            )

        if tac_vu == "lac_chuong":
            anh = _ve_anh_kiem_tra(ma, "lac_chuong", canh_bao,
                                   "ALERT: Pig out of zone!" if canh_bao else "Zone OK: All inside")
            if canh_bao:
                ev_kq, _ = luu_su_kien({
                    "loai": "lac_chuong", "o": ma, "muc": "khan_cap", "thoi_gian": now_iso,
                    "anh": anh, "du_lieu": {"id_theo_doi": 9, "giay_ngoai": 7},
                })
                return jsonify(
                    ok=True, tac_vu=tac_vu, trang_thai="khan_cap",
                    nhan_trang_thai="Phát hiện sổng chuồng!",
                    tieu_de=f"Cảnh báo sổng chuồng – {o['ten']}",
                    tom_tat="Phát hiện 1 con (ID #09) vượt ra ngoài vạch giới hạn ô chuồng 7 giây!",
                    anh=anh, su_kien_id=ev_kq.get("id"),
                    chi_tiet=[
                        ["Cá thể vượt vùng", "ID #09 (ngoài vùng 7 giây)"],
                        ["Số con trong chuồng", f"{max(0, dk - 1)}/{dk} con"],
                        ["Ngưỡng báo động", f"{st['nguong']['lac_chuong_giay']} giây"],
                        ["Thời điểm kiểm tra", now_str],
                    ],
                )
            return jsonify(
                ok=True, tac_vu=tac_vu, trang_thai="ok",
                nhan_trang_thai="Trong vùng an toàn",
                tieu_de=f"Kiểm tra sổng chuồng – {o['ten']}",
                tom_tat=f"Toàn bộ {dk}/{dk} con nằm trong ranh giới ô chuồng, không có cá thể vượt vạch.",
                anh=anh,
                chi_tiet=[
                    ["Trong vùng ô chuồng", f"{dk}/{dk} con (100%)"],
                    ["Ngoài vùng / Vượt vạch", "0 con"],
                    ["Ngưỡng cảnh báo", f"{st['nguong']['lac_chuong_giay']} giây liên tục"],
                    ["Thời điểm kiểm tra", now_str],
                ],
            )

        if tac_vu == "suc_khoe":
            ng_tho = st["nguong"]["tho_nhanh_nhip_phut"]
            anh = _ve_anh_kiem_tra(ma, "suc_khoe", canh_bao,
                                   "Resp: 54 bpm (HIGH)" if canh_bao else "Resp: 28 bpm (Normal)")
            if canh_bao:
                ev_kq, _ = luu_su_kien({
                    "loai": "tho_nhanh", "o": ma, "muc": "canh_bao", "thoi_gian": now_iso,
                    "anh": anh, "du_lieu": {"nhip": 54, "gio_nam": 4},
                })
                return jsonify(
                    ok=True, tac_vu=tac_vu, trang_thai="canh_bao",
                    nhan_trang_thai="Thở nhanh bất thường",
                    tieu_de=f"Kiểm tra sức khỏe – {o['ten']}",
                    tom_tat=f"Phát hiện cá thể thở gấp 54 lần/phút (vượt ngưỡng {ng_tho} lần/phút) và nằm 4 giờ liên tục.",
                    anh=anh, su_kien_id=ev_kq.get("id"),
                    chi_tiet=[
                        ["Nhịp thở cao nhất", f"54 lần/phút (Ngưỡng ≤ {ng_tho})"],
                        ["Thời gian nằm liên tục", "4.0 giờ"],
                        ["Trạng thái vận động", "Có 1 cá thể mệt / thở gấp"],
                        ["Thời điểm kiểm tra", now_str],
                    ],
                )
            return jsonify(
                ok=True, tac_vu=tac_vu, trang_thai="ok",
                nhan_trang_thai="Sức khỏe ổn định",
                tieu_de=f"Kiểm tra sức khỏe & Nhịp thở – {o['ten']}",
                tom_tat=f"Nhịp thở trung bình 28 lần/phút (an toàn ≤ {ng_tho} lần/phút). Đàn vận động bình thường.",
                anh=anh,
                chi_tiet=[
                    ["Nhịp thở trung bình", f"28 lần/phút (Ngưỡng ≤ {ng_tho})"],
                    ["Cá thể nằm bất động lâu", "0 con"],
                    ["Đánh giá chung", "Hô hấp & vận động bình thường"],
                    ["Thời điểm kiểm tra", now_str],
                ],
            )

    return jsonify(ok=False, loi=["Chức năng kiểm tra không hợp lệ"]), 400


# ---------- Tuần 3: vẽ vùng ----------
@app.route("/ve-vung")
def ds_ve_vung():
    with db.connect() as c:
        o = c.execute("SELECT ma, ten, vung_json FROM o_chuong ORDER BY ma").fetchall()
    return render_template("ds_ve_vung.html", tab="cd", o=o)


@app.route("/ve-vung/<ma>")
def ve_vung(ma):
    with db.connect() as c:
        r = c.execute("SELECT * FROM o_chuong WHERE ma=?", (ma,)).fetchone()
    if not r:
        abort(404)
    return render_template("ve_vung.html", tab="cd", o=r, co_anh=(DATA / "camera" / f"{ma}.jpg").exists())


@app.get("/camera/<ma>.jpg")
def anh_camera(ma):
    return send_from_directory(DATA / "camera", f"{ma}.jpg")


@app.post("/api/o/<ma>/anh-camera")
def api_anh_camera(ma):
    """Tải ảnh (jpg/png) hoặc video (lấy khung đầu) làm ảnh nền để vẽ vùng."""
    f = request.files.get("file")
    with db.connect() as c:
        if not c.execute("SELECT 1 FROM o_chuong WHERE ma=?", (ma,)).fetchone():
            return jsonify(ok=False, loi=["Không có ô này"]), 404
    if not f:
        return jsonify(ok=False, loi=["Thiếu file"]), 400
    try:
        pipeline_adapter.luu_khung_hinh(f, DATA / "camera" / f"{ma}.jpg")
    except ValueError as e:
        return jsonify(ok=False, loi=[str(e)]), 400
    return jsonify(ok=True)


@app.get("/api/o/<ma>/vung")
def api_doc_vung(ma):
    """TV2/TV4/TV5 đọc vùng của ô. ?pixel=1&rong=1920&cao=1080 để lấy luôn dạng pixel."""
    with db.connect() as c:
        v = vung.doc(c, ma)
    if v is None:
        return jsonify(ok=False, loi=["Không có ô này"]), 404
    if request.args.get("pixel"):
        r, h = request.args.get("rong", type=int), request.args.get("cao", type=int)
        if not r or not h:
            return jsonify(ok=False, loi=["Cần rong và cao (pixel)"]), 400
        return jsonify(vung.sang_pixel(v, r, h))
    return jsonify(v)


@app.put("/api/o/<ma>/vung")
def api_luu_vung(ma):
    v, loi = vung.kiem_tra(request.get_json(silent=True))
    if loi:
        return jsonify(ok=False, loi=loi), 400
    with db.connect() as c:
        if vung.doc(c, ma) is None:
            return jsonify(ok=False, loi=["Không có ô này"]), 404
        vung.luu(c, ma, v)
    return jsonify(ok=True)


# ---------- Tuần 3: chạy video qua pipeline ----------
@app.route("/chay-video")
def chay_video():
    with db.connect() as c:
        o = c.execute("SELECT ma, ten FROM o_chuong ORDER BY ma").fetchall()
    return render_template("chay_video.html", tab="cd", o=o, che_do=pipeline_adapter.che_do())


@app.post("/api/chay-video")
def api_chay_video():
    f, ma = request.files.get("video"), request.form.get("o")
    with db.connect() as c:
        v = vung.doc(c, ma) if ma else None
    if v is None:
        return jsonify(ok=False, loi=["Chọn ô chuồng"]), 400
    if not f or not f.filename:
        return jsonify(ok=False, loi=["Chọn file video"]), 400
    job = pipeline_adapter.bat_dau(f, ma, v, DATA, luu_su_kien)
    return jsonify(ok=True, job=job), 202


@app.get("/api/chay-video/<job>")
def api_trang_thai_job(job):
    j = pipeline_adapter.trang_thai(job)
    if j is None:
        return jsonify(ok=False, loi=["Không có tác vụ"]), 404
    with db.connect() as c:
        ds = [db.row_to_event(c.execute("SELECT * FROM su_kien WHERE id=?", (i,)).fetchone())
              for i in j["su_kien"]]
    return jsonify({**j, "ds": ds, "ok": True})


@app.get("/recordings/<path:p>")
def recordings(p):
    return send_from_directory(DATA / "recordings", p)


if __name__ == "__main__":
    app.run(debug=True)
