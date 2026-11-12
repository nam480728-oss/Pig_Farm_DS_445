"""Cơ sở dữ liệu SQLite cho webapp giám sát trang trại lợn."""
import json
import os
import sqlite3
from pathlib import Path

# TT_DATA: thư mục dữ liệu khác (dùng cho kiểm thử, không đụng DB thật)
DB_PATH = Path(os.environ.get("TT_DATA") or Path(__file__).parent / "data") / "trang_trai.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS o_chuong (
    ma          TEXT PRIMARY KEY,          -- A, B, C...
    ten         TEXT NOT NULL,
    so_dang_ky  INTEGER NOT NULL DEFAULT 0, -- số con chủ đăng ký trong ô
    camera      TEXT,                       -- đường dẫn/URL camera hoặc video
    vung_json   TEXT                        -- đa giác ô, máng ăn, vạch lạc chuồng (tuần 3)
);

CREATE TABLE IF NOT EXISTS dan (
    ma          TEXT PRIMARY KEY,
    o           TEXT NOT NULL REFERENCES o_chuong(ma),
    so_con      INTEGER NOT NULL,
    ngay_nhap   TEXT NOT NULL,
    kg_nhap_tb  REAL,
    moc_kg_ngay REAL NOT NULL DEFAULT 0.7   -- mốc tăng trưởng chuẩn (kg/ngày) từ ngày nhập
);

CREATE TABLE IF NOT EXISTS lan_do (          -- mỗi lần đo cân nặng một con
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    dan         TEXT NOT NULL REFERENCES dan(ma),
    con_id      TEXT NOT NULL,              -- ID theo dõi / mã con
    thoi_gian   TEXT NOT NULL,
    kg          REAL NOT NULL,
    anh         TEXT
);

CREATE TABLE IF NOT EXISTS su_kien (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    loai          TEXT NOT NULL,
    o             TEXT NOT NULL,
    thoi_gian     TEXT NOT NULL,
    muc           TEXT NOT NULL,            -- khan_cap | canh_bao | thong_tin
    anh           TEXT,
    du_lieu       TEXT NOT NULL DEFAULT '{}', -- JSON
    trang_thai    TEXT NOT NULL DEFAULT 'moi', -- moi | dung | bao_nham
    hien_ngay     INTEGER NOT NULL DEFAULT 0   -- lớp thông báo quyết định: hiện banner ngay
);
CREATE INDEX IF NOT EXISTS ix_su_kien_tg ON su_kien(thoi_gian DESC);

CREATE TABLE IF NOT EXISTS cai_dat (
    khoa     TEXT PRIMARY KEY,
    gia_tri  TEXT NOT NULL                  -- JSON
);
"""

DEFAULT_SETTINGS = {
    "gio_canh_gac": {"bat": True, "tu": "20:00", "den": "05:00"},
    "gio_dem": {"bat": True, "tu": "07:00", "den": "07:15", "phut": 15},
    "gio_cho_an": ["06:30", "11:30", "17:00"],
    "tu_dong": {
        "dem_lon": True,
        "canh_gac": True,
        "phat_trien": True,
        "phat_trien_tu": "08:00",
        "phat_trien_den": "09:00",
        "an_uong": True,
        "phut_an": 30,
        "lac_chuong": True,
        "lac_chuong_tu": "00:00",
        "lac_chuong_den": "23:59",
        "suc_khoe": True,
        "suc_khoe_tu": "00:00",
        "suc_khoe_den": "23:59",
    },
    "nguong": {
        "lac_chuong_giay": 5,
        "lac_chuong_bao_lai_phut": 5,
        "nguoi_khung_lien_tiep": 10,
        "dem_giu_giay": 5,
        "tho_nhanh_nhip_phut": 40,
        "coi_phan_tram": 15,
        "lon_nhanh_phan_tram": 15,
    },
}


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as c:
        c.executescript(SCHEMA)
        for k, v in DEFAULT_SETTINGS.items():
            c.execute("INSERT OR IGNORE INTO cai_dat(khoa, gia_tri) VALUES (?, ?)",
                      (k, json.dumps(v, ensure_ascii=False)))


def get_settings(conn):
    """Đọc cài đặt; khoá con mới thêm ở bản sau (trong DEFAULT_SETTINGS) tự có giá trị mặc định."""
    st = {r["khoa"]: json.loads(r["gia_tri"]) for r in conn.execute("SELECT * FROM cai_dat")}
    for k, v in DEFAULT_SETTINGS.items():
        if isinstance(v, dict):
            st[k] = {**v, **st.get(k, {})}
        else:
            st.setdefault(k, v)
    return st


def row_to_event(r):
    d = dict(r)
    d["du_lieu"] = json.loads(d["du_lieu"] or "{}")
    return d
