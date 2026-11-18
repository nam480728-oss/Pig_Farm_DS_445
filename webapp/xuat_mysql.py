"""Xuất cơ sở dữ liệu SQLite (data/trang_trai.db) sang file SQL chuẩn MySQL để chạy trên Navicat.

Cách dùng:
  python xuat_mysql.py
  -> Sinh ra file trang_trai_mysql.sql (mở bằng Navicat -> Execute SQL File...).

Tuỳ chọn nạp thẳng vào MySQL server (cần cài pymysql hoặc mysql-connector-python):
  python xuat_mysql.py --host 127.0.0.1 --port 3306 --user root --password "" --db trang_trai
"""
import argparse
from pathlib import Path

import db
import seed

DEFAULT_OUT = Path(__file__).parent / "trang_trai_mysql.sql"

MYSQL_SCHEMA = """-- Cơ sở dữ liệu hệ thống giám sát trang trại lợn (xuất cho MySQL / Navicat)
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS `{db_name}`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE `{db_name}`;

DROP TABLE IF EXISTS `lan_do`;
DROP TABLE IF EXISTS `su_kien`;
DROP TABLE IF EXISTS `dan`;
DROP TABLE IF EXISTS `cai_dat`;
DROP TABLE IF EXISTS `o_chuong`;

CREATE TABLE `o_chuong` (
    `ma`         VARCHAR(50)  NOT NULL,
    `ten`        VARCHAR(255) NOT NULL,
    `so_dang_ky` INT          NOT NULL DEFAULT 0,
    `camera`     VARCHAR(500) NULL,
    `vung_json`  LONGTEXT     NULL,
    PRIMARY KEY (`ma`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `dan` (
    `ma`          VARCHAR(50) NOT NULL,
    `o`           VARCHAR(50) NOT NULL,
    `so_con`      INT         NOT NULL,
    `ngay_nhap`   VARCHAR(50) NOT NULL,
    `kg_nhap_tb`  DOUBLE      NULL,
    `moc_kg_ngay` DOUBLE      NOT NULL DEFAULT 0.7,
    PRIMARY KEY (`ma`),
    CONSTRAINT `fk_dan_o_chuong` FOREIGN KEY (`o`) REFERENCES `o_chuong`(`ma`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `lan_do` (
    `id`        INT          NOT NULL AUTO_INCREMENT,
    `dan`       VARCHAR(50)  NOT NULL,
    `con_id`    VARCHAR(100) NOT NULL,
    `thoi_gian` VARCHAR(50)  NOT NULL,
    `kg`        DOUBLE       NOT NULL,
    `anh`       VARCHAR(500) NULL,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_lan_do_dan` FOREIGN KEY (`dan`) REFERENCES `dan`(`ma`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `su_kien` (
    `id`         INT          NOT NULL AUTO_INCREMENT,
    `loai`       VARCHAR(50)  NOT NULL,
    `o`          VARCHAR(50)  NOT NULL,
    `thoi_gian`  VARCHAR(50)  NOT NULL,
    `muc`        VARCHAR(50)  NOT NULL,
    `anh`        VARCHAR(500) NULL,
    `du_lieu`    LONGTEXT     NOT NULL,
    `trang_thai` VARCHAR(50)  NOT NULL DEFAULT 'moi',
    `hien_ngay`  TINYINT(1)   NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    INDEX `ix_su_kien_tg` (`thoi_gian` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `cai_dat` (
    `khoa`    VARCHAR(100) NOT NULL,
    `gia_tri` LONGTEXT     NOT NULL,
    PRIMARY KEY (`khoa`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

TABLES = [
    ("o_chuong", ["ma", "ten", "so_dang_ky", "camera", "vung_json"]),
    ("dan", ["ma", "o", "so_con", "ngay_nhap", "kg_nhap_tb", "moc_kg_ngay"]),
    ("lan_do", ["id", "dan", "con_id", "thoi_gian", "kg", "anh"]),
    ("su_kien", ["id", "loai", "o", "thoi_gian", "muc", "anh", "du_lieu", "trang_thai", "hien_ngay"]),
    ("cai_dat", ["khoa", "gia_tri"]),
]


def _sql_val(v):
    """Chuyển giá trị Python từ SQLite thành literal SQL an toàn cho MySQL."""
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float)):
        return str(v)
    s = (
        str(v)
        .replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\r", "\\r")
        .replace("\n", "\\n")
        .replace("\0", "\\0")
    )
    return f"'{s}'"


def tao_sql(db_name="trang_trai"):
    """Đọc data/trang_trai.db và trả về (nội_dung_sql, thống_kê_dòng)."""
    if not db.DB_PATH.exists():
        seed.main()
    with db.connect() as c:
        if c.execute("SELECT COUNT(*) FROM o_chuong").fetchone()[0] == 0:
            seed.main()

    lines = [MYSQL_SCHEMA.format(db_name=db_name)]
    counts = {}

    with db.connect() as c:
        for table, cols in TABLES:
            rows = c.execute(f"SELECT {', '.join(cols)} FROM {table}").fetchall()
            counts[table] = len(rows)
            if not rows:
                continue
            col_list = ", ".join(f"`{col}`" for col in cols)
            lines.append(f"\n-- Dữ liệu bảng `{table}` ({len(rows)} dòng)")
            values = []
            for r in rows:
                vals = ", ".join(_sql_val(r[col]) for col in cols)
                values.append(f"({vals})")
            lines.append(f"INSERT INTO `{table}` ({col_list}) VALUES\n" + ",\n".join(values) + ";")

    lines.append("\nSET FOREIGN_KEY_CHECKS = 1;\n")
    return "\n".join(lines), counts


def nap_mysql(sql_text, host, port, user, password):
    """Thực thi từng câu lệnh SQL trực tiếp lên MySQL server nếu có driver."""
    conn = None
    try:
        import pymysql
        conn = pymysql.connect(host=host, port=port, user=user, password=password, charset="utf8mb4")
    except ImportError:
        try:
            import mysql.connector
            conn = mysql.connector.connect(host=host, port=port, user=user, password=password, charset="utf8mb4")
        except ImportError as exc:
            raise RuntimeError(
                "Chưa cài driver MySQL (pymysql hoặc mysql-connector-python). "
                "Hãy dùng file .sql vừa xuất để chạy trong Navicat."
            ) from exc

    try:
        cur = conn.cursor()
        # Tách theo dấu ';' ở cuối dòng để thực thi lần lượt
        for stmt in sql_text.split(";\n"):
            s = stmt.strip()
            if s:
                cur.execute(s)
        conn.commit()
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Xuất DB trang trại lợn sang MySQL (Navicat)")
    parser.add_argument("--db", default="trang_trai", help="Tên database MySQL (mặc định: trang_trai)")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Đường dẫn file .sql xuất ra")
    parser.add_argument("--host", help="Host MySQL nếu muốn nạp trực tiếp (vd: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=3306, help="Cổng MySQL (mặc định: 3306)")
    parser.add_argument("--user", default="root", help="Username MySQL")
    parser.add_argument("--password", default="", help="Mật khẩu MySQL")
    args = parser.parse_args()

    sql_text, counts = tao_sql(db_name=args.db)
    out_path = Path(args.out)
    out_path.write_text(sql_text, encoding="utf-8")

    print(f"Đã xuất file MySQL: {out_path}")
    for tbl, cnt in counts.items():
        print(f"  - {tbl}: {cnt} dòng")

    if args.host:
        nap_mysql(sql_text, args.host, args.port, args.user, args.password)
        print(f"Đã nạp thành công vào MySQL ({args.host}:{args.port}/{args.db}).")


if __name__ == "__main__":
    main()
