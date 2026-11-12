# Định dạng sự kiện (mục 8) — gửi cho TV2, TV4, TV5

Gửi bằng HTTP:  `POST http://<máy-webapp>:5000/api/su-kien`  (JSON)

| Trường | Bắt buộc | Ví dụ | Ghi chú |
|---|---|---|---|
| loai | ✔ | `nghi_chet` | `dem_thieu, dem_du, nguoi_la, nghi_trom, lac_chuong, nghi_chet, tho_nhanh, bo_an, o_an_kem` |
| o | ✔ | `A` | Mã ô chuồng, phải có trong hệ thống |
| thoi_gian | ✔ | `2026-11-10T02:14:00` | ISO 8601 |
| muc | ✔ | `khan_cap` | `khan_cap`, `canh_bao`, `thong_tin` |
| anh |  | `recordings/su_kien/123.jpg` | Ảnh đã khoanh hộp |
| du_lieu |  | `{"nhip": null, "gio_nam": 4}` | Số liệu thêm tuỳ loại |

Trả về: `201 {"ok": true, "id": 13}` hoặc `400 {"ok": false, "loi": [...]}`.

Ví dụ:

```python
import requests
requests.post("http://127.0.0.1:5000/api/su-kien", json={
    "loai": "lac_chuong", "o": "B", "thoi_gian": "2026-11-10T02:14:00",
    "muc": "khan_cap", "anh": "recordings/su_kien/123.jpg",
    "du_lieu": {"id_theo_doi": 12, "giay_ngoai": 6}})
```

Luôn hiện ngay: `nghi_trom`, `lac_chuong`, `nghi_chet`. Các loại còn lại: lớp thông báo quyết định (tuần 2).

Báo cáo phát triển trả về riêng một khối (làm ở tuần 4): trung bình đàn, tăng kg và %, độ đồng đều,
danh sách con còi và con lớn nhanh (mỗi con: ảnh, kg, chênh so với mốc, chênh so với trung bình đàn).

## Ghi cân nặng cho báo cáo phát triển (TV2)
`POST /api/lan-do` — mỗi lần đo cả đàn một lượt:
```python
requests.post("http://127.0.0.1:5000/api/lan-do", json={
    "dan": "D01", "thoi_gian": "2026-11-08T08:00:00",
    "ds": [{"con_id": "D01-03", "kg": 71.2, "anh": "recordings/con/D01-03.jpg"}, ...]})
```
Webapp tự tính báo cáo (`GET /api/dan/D01/bao-cao`: trung bình, tăng kg/%, độ đồng đều, con còi, con lớn nhanh,
chênh so với mốc và so với TB đàn). Định nghĩa từng chỉ số nằm ở đầu `phat_trien.py`.

## Kiểm thử toàn hệ thống
`python kiem_thu.py` — chạy trên DB tạm, thử mọi loại sự kiện, báo cáo, vùng, chạy video.
