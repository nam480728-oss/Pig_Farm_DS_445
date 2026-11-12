# Vùng vẽ trên camera — cho TV2 (Nam), TV4 (Bảo Nguyên), TV5 (Mai Nguyên)

Chủ trại vẽ vùng trong webapp: **Cài đặt → Vẽ vùng trên ảnh camera**. Code đọc vùng qua API.

## Đọc vùng
```python
import requests
# Dạng tỉ lệ 0–1 (không phụ thuộc độ phân giải)
v = requests.get("http://127.0.0.1:5000/api/o/A/vung").json()
# Dạng pixel của video (khuyến nghị)
v = requests.get("http://127.0.0.1:5000/api/o/A/vung",
                 params={"pixel": 1, "rong": 1920, "cao": 1080}).json()
```

## Cấu trúc (khoá nào chưa vẽ thì không có)
| Khoá | Nội dung | Dùng cho |
|---|---|---|
| `o` | đa giác ô, `[[x,y],…]` ≥ 3 điểm | đếm lợn trong ô (TV5), PolygonZone |
| `mang_an` | danh sách đa giác máng ăn | module bỏ ăn (TV2) |
| `lac_chuong` | `{"kieu":"vung","diem":[…]}` = vùng NGOÀI ô, hoặc `{"kieu":"vach","diem":[p1,p2],"diem_ngoai":p}` = vạch mức, `diem_ngoai` là điểm nằm phía ngoài vạch | sổng chuồng (TV4) |
| `vat_tham_chieu` | `{"diem":[p1,p2],"cm":80}`; dạng pixel có thêm `cm_moi_pixel` | đổi pixel → cm cho cân nặng (TV2) |

Xác định phía ngoài của vạch: lấy dấu của tích có hướng `(p2-p1) × (điểm-p1)`;
lợn ở phía ngoài khi dấu giống dấu của `diem_ngoai`. "Ra hẳn" = cả 4 góc bounding box ở phía ngoài.

## Hợp đồng chạy video (để webapp gọi pipeline của Nam)
`ai/pipeline.py` cần có:
```python
def chay_video(nguon, o, vung, on_event, tien_do=None): ...
```
- `vung`: dict pixel như trên; `on_event(dict)`: sự kiện đúng mục 8 (xem dinh_dang_su_kien.md).
- Ảnh khoanh đỏ lưu vào `data/recordings/su_kien/`, trường `anh` ghi `recordings/su_kien/<tên>.jpg`.
Chưa có file này thì trang "Chạy video" dùng bản giả (MOCK).
