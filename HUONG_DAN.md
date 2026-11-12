# Hướng dẫn chi tiết: Webapp giám sát trang trại lợn

Tài liệu cho Thành viên 3 (webapp) và cho các thành viên nối vào webapp (TV2, TV4, TV5).
Mọi ví dụ dưới đây khớp với code trong thư mục `webapp/`.

## Mục lục
1. [Cài đặt và chạy](#1-cài-đặt-và-chạy)
2. [Cấu trúc thư mục](#2-cấu-trúc-thư-mục)
3. [Dữ liệu mẫu](#3-dữ-liệu-mẫu)
4. [Hướng dẫn sử dụng từng trang](#4-hướng-dẫn-sử-dụng-từng-trang)
5. [Vẽ vùng trên ảnh camera](#5-vẽ-vùng-trên-ảnh-camera)
6. [Quy tắc thông báo (banner)](#6-quy-tắc-thông-báo-banner)
7. [Báo cáo phát triển của đàn](#7-báo-cáo-phát-triển-của-đàn)
8. [Tích hợp: dành cho TV2, TV4, TV5](#8-tích-hợp-dành-cho-tv2-tv4-tv5)
9. [Tham chiếu API](#9-tham-chiếu-api)
10. [Chạy video qua pipeline](#10-chạy-video-qua-pipeline)
11. [Quay video demo](#11-quay-video-demo)
12. [Kiểm thử](#12-kiểm-thử)
13. [Xử lý sự cố](#13-xử-lý-sự-cố)

---

## 1. Cài đặt và chạy

Yêu cầu: Python 3.10 trở lên.

```bash
cd webapp
pip install -r requirements.txt     # flask, opencv-python-headless, numpy
python seed.py                      # tạo dữ liệu mẫu (XOÁ dữ liệu cũ)
python app.py                       # mở http://127.0.0.1:5000
```

- Giao diện là khung điện thoại rộng tối đa 420 px. Trên máy tính, thu hẹp cửa sổ hoặc bật chế độ điện thoại của DevTools để xem đúng dạng.
- Xem trên điện thoại cùng mạng Wi-Fi: chạy `flask --app app run --host 0.0.0.0`, rồi mở `http://<IP máy tính>:5000` trên điện thoại.
- Chế độ sáng hoặc tối theo cài đặt của hệ điều hành.

Lưu ý: `python seed.py` luôn xoá cơ sở dữ liệu cũ rồi tạo lại. Chỉ chạy khi muốn bắt đầu từ dữ liệu mẫu.

## 2. Cấu trúc thư mục

```
webapp/
  app.py               Các trang và API (Flask)
  db.py                Kết nối SQLite, schema, cài đặt mặc định
  events.py            Định dạng sự kiện và kiểm tra (mục 8 của phân công)
  thong_bao.py         Quyết định hiện banner hay chỉ lưu; kiểm tra cài đặt
  vung.py              Lưu, kiểm tra vùng vẽ; đổi sang pixel
  phat_trien.py        Tính báo cáo phát triển của đàn
  pipeline_adapter.py  Cầu nối với pipeline của TV2; bản giả (MOCK)
  seed.py              Tạo dữ liệu mẫu
  simulate.py          Gửi sự kiện giả để thử banner
  demo.py              Phát sự kiện theo kịch bản demo 2 phút
  kiem_thu.py          Kiểm thử toàn hệ thống
  templates/, static/  Giao diện (HTML, CSS, JS thuần)
  docs/                Tài liệu cho các thành viên khác
  data/                Tạo tự động khi chạy (xem bên dưới)
```

Thư mục `data/` (không nộp lên git):

| Đường dẫn | Nội dung |
|---|---|
| `data/trang_trai.db` | Cơ sở dữ liệu SQLite |
| `data/camera/<ô>.jpg` | Ảnh nền để vẽ vùng của từng ô |
| `data/videos/` | Video tải lên ở trang Chạy video |
| `data/recordings/su_kien/` | Ảnh khoanh đỏ của sự kiện |
| `data/recordings/con/` | Ảnh từng con (báo cáo phát triển) |

Biến môi trường `TT_DATA=<thư mục>` đổi nơi lưu dữ liệu (dùng cho kiểm thử, không đụng dữ liệu thật).

## 3. Dữ liệu mẫu

`seed.py` tạo:

- 4 ô: A (20 con), B (18), C (25), D (8); mỗi ô có một ảnh camera giả lập.
- 3 đàn: D01 (ô A), D02 (ô B), D03 (ô C), mỗi đàn có các lần đo hằng tuần. Con số 01 của mỗi đàn là con còi, con số 02 là con lớn nhanh, để báo cáo có dữ liệu thử.
- 12 sự kiện đủ các loại.
- Cài đặt mặc định: canh gác bật 20:00 đến 05:00; đếm lúc 07:00 trong 15 phút; cho ăn 06:30, 11:30, 17:00.

## 4. Hướng dẫn sử dụng từng trang

Thanh tab dưới cùng có 5 mục.

### Trang chủ
- Hai số lớn: tổng số lợn đăng ký, số sự kiện khẩn cấp chưa xử lý (đỏ khi lớn hơn 0).
- Lưới các ô. Chấm đỏ cạnh tên ô nghĩa là ô đó có sự kiện khẩn cấp chưa trả lời.
- Bốn sự kiện gần nhất, có nút Đúng và Báo nhầm.

### Ô chuồng
Mỗi ô hiện số con đăng ký, số đếm gần nhất, số sự kiện mới, đã vẽ vùng chưa, và liên kết vào công cụ vẽ vùng.

### Đàn
- Danh sách đàn: cân nặng trung bình, mức tăng so với kỳ trước, độ đồng đều, số con còi và lớn nhanh.
- Bấm vào một đàn có 3 tab:
  - **Tổng quan**: bốn số chính và biểu đồ trung bình đàn so với mốc.
  - **Con còi** và **Con lớn nhanh**: mỗi con có ảnh, cân nặng, chênh so với mốc và chênh so với trung bình đàn.

### Sự kiện
Toàn bộ sự kiện (100 mới nhất), lọc theo mức: Tất cả, Khẩn cấp, Cảnh báo, Thông tin. Mỗi sự kiện có thể bấm:
- **Đúng**: xác nhận cảnh báo chính xác.
- **Báo nhầm**: đánh dấu cảnh báo sai.

Trạng thái được lưu (`moi`, `dung`, `bao_nham`). Hiện tại webapp chỉ ghi nhận, chưa tự chỉnh ngưỡng theo phản hồi.

### Cài đặt
Sửa rồi bấm **Lưu cài đặt**:

| Mục | Ràng buộc |
|---|---|
| Giờ canh gác: bật, từ, đến | Giờ dạng HH:MM; hỗ trợ qua nửa đêm (20:00 đến 05:00) |
| Giờ đếm: bắt đầu, thời lượng | Thời lượng 10 đến 20 phút |
| Giờ cho ăn | Danh sách HH:MM cách nhau dấu phẩy |
| Ngưỡng | Mọi giá trị phải là số lớn hơn 0 |

Các ngưỡng: ngoài chuồng liên tục (giây), báo lại sau (phút), số khung liên tiếp người lạ, giữ mức đếm cao nhất (giây), nhịp thở nhanh (nhịp/phút), con còi (% thấp hơn trung bình đàn), con lớn nhanh (% cao hơn trung bình đàn).

Cài đặt cũng có lối vào **Vẽ vùng trên ảnh camera** và **Chạy video demo**.

### Banner thông báo
Khi có sự kiện cần báo ngay, banner trượt xuống đầu màn hình (ở mọi trang):
- Màu đỏ là khẩn cấp, cam là cảnh báo, xanh là thông tin.
- Nhiều sự kiện xếp hàng, hiện "+N". Bấm **Đúng** hoặc **Báo nhầm** để chuyển sang sự kiện kế tiếp; bấm dấu ✕ để bỏ qua.
- Hàng đợi được giữ khi chuyển trang. Đóng hẳn tab trình duyệt thì mất hàng đợi (sự kiện vẫn nằm trong trang Sự kiện).

## 5. Vẽ vùng trên ảnh camera

Vào **Cài đặt → Vẽ vùng trên ảnh camera → chọn ô**.

1. **Ảnh nền**: nếu chưa có ảnh thật, kéo xuống phần "Ảnh nền" và chọn ảnh (jpg, png) hoặc video (mp4, avi, mov, mkv). Với video, hệ thống lấy khung hình đầu tiên.
2. Chọn công cụ ở trên cùng, rồi chạm lên ảnh:

| Công cụ | Cách vẽ |
|---|---|
| Ô chuồng | Chạm các góc (ít nhất 3), bấm **Xong hình** |
| Máng ăn | Như trên; vẽ thêm máng khác nếu có |
| Lạc chuồng (vùng ngoài) | Chạm các góc của vùng nằm NGOÀI ô, bấm **Xong hình** |
| Lạc chuồng (vạch) | Chạm 2 đầu vạch, rồi 1 điểm ở PHÍA NGOÀI vạch (tự hoàn tất sau lần chạm thứ ba) |
| Vật tham chiếu | Chạm 2 đầu của vật có độ dài đã biết, nhập độ dài thật (cm) |

3. **Hoàn tác** bỏ điểm vừa chạm; **Xoá hình này** xoá hình của công cụ đang chọn.
4. Bấm **Lưu vùng**. Còn hình vẽ dở thì phải Xong hình hoặc Xoá trước khi lưu.

Tọa độ lưu theo tỉ lệ 0 đến 1 nên dùng được với mọi độ phân giải video. Các mô-đun AI đọc vùng qua API (mục 9.3), không phải vẽ lại.

## 6. Quy tắc thông báo (banner)

Mỗi sự kiện vào được xét theo thứ tự, cột `hien_ngay` ghi kết quả:

| Ưu tiên | Điều kiện | Kết quả |
|---|---|---|
| 1 | `nghi_trom`, `lac_chuong`, `nghi_chet` | Luôn hiện ngay |
| 2 | Mức `khan_cap` | Hiện ngay |
| 3 | `nguoi_la` | Hiện ngay chỉ khi canh gác bật và sự kiện nằm trong giờ canh gác; còn lại chỉ lưu |
| 4 | Mức `canh_bao` | Hiện ngay |
| 5 | Mức `thong_tin` (ví dụ `dem_du`) | Chỉ lưu |

Muốn đổi quy tắc: sửa hàm `quyet_dinh` trong `thong_bao.py`.

## 7. Báo cáo phát triển của đàn

Tính từ các lần đo trong bảng `lan_do` (định nghĩa ở đầu `phat_trien.py`):

| Chỉ số | Cách tính |
|---|---|
| Mốc (kg) | Kg nhập trung bình + hệ số kg/ngày của đàn × số ngày tuổi (mặc định 0,7; đàn mẫu D03 dùng 0,4) |
| Trung bình đàn | Trung bình kg các con ở ngày đo gần nhất |
| Tăng kg và % | So với ngày đo liền trước, chỉ tính các con có mặt ở cả hai ngày |
| Độ đồng đều | % số con có kg trong ±10% trung bình đàn; kèm CV% |
| Con còi | Kg ≤ trung bình × (1 − ngưỡng còi), mặc định 15% |
| Con lớn nhanh | Kg ≥ trung bình × (1 + ngưỡng lớn nhanh), mặc định 15% |
| Chênh của từng con | Kg trừ mốc, và kg trừ trung bình đàn |

Hệ số mốc (`dan.moc_kg_ngay`) hiện đặt tay; nên thay bằng số thật của trại hoặc bảng giống.

## 8. Tích hợp: dành cho TV2, TV4, TV5

Webapp chạy ở `http://<máy-webapp>:5000`. Các mô-đun chỉ cần gọi HTTP, không cần import code webapp.

### 8.1 Checklist cho mô-đun gửi sự kiện
- [ ] Ô chuồng đã có trong hệ thống (mã `A`, `B`, ... khớp với `ô` trong sự kiện).
- [ ] Gửi đúng 4 trường bắt buộc: `loai`, `o`, `thoi_gian`, `muc`.
- [ ] `thoi_gian` dạng ISO, ví dụ `2026-11-10T02:14:00`.
- [ ] Ảnh khoanh đỏ lưu dưới `data/recordings/su_kien/`, trường `anh` ghi `recordings/su_kien/<tên>.jpg`.
- [ ] Kiểm tra mã trả về: 201 là thành công, 400 kèm danh sách lỗi.

### 8.2 Các loại sự kiện

| `loai` | Ý nghĩa | `muc` thường dùng |
|---|---|---|
| `dem_thieu` | Đếm được ít hơn số đăng ký | `canh_bao` |
| `dem_du` | Đếm đủ | `thong_tin` |
| `nguoi_la` | Phát hiện người | `canh_bao` |
| `nghi_trom` | Người lạ trong giờ canh gác | `khan_cap` |
| `lac_chuong` | Lợn ra ngoài vùng | `khan_cap` |
| `nghi_chet` | Nằm bất động, không có nhịp thở | `khan_cap` |
| `tho_nhanh` | Nhịp thở nhanh | `canh_bao` |
| `bo_an` | Nghi bỏ ăn | `canh_bao` |
| `o_an_kem` | Cả ô ăn kém | `canh_bao` |

Mức (`muc`) do mô-đun gửi quyết định; webapp chỉ kiểm tra giá trị hợp lệ.

### 8.3 Trường `du_lieu` gợi ý
Tự do theo từng loại (object JSON). Các khoá sau được hiển thị bằng nhãn tiếng Việt, khoá khác hiển thị nguyên tên:

`nhip` (nhịp thở), `gio_nam` (giờ đã nằm), `diem_nghi_van`, `ty_le_an`, `dem`, `dang_ky`, `so_nguoi`, `khung`, `id_theo_doi`, `giay_ngoai`.

### 8.4 Ví dụ Python

```python
import requests
URL = "http://127.0.0.1:5000"

# Gửi sự kiện
r = requests.post(f"{URL}/api/su-kien", json={
    "loai": "lac_chuong", "o": "B", "muc": "khan_cap",
    "thoi_gian": "2026-11-10T02:14:00",
    "anh": "recordings/su_kien/123.jpg",
    "du_lieu": {"id_theo_doi": 12, "giay_ngoai": 6}})
print(r.status_code, r.json())   # 201 {'ok': True, 'id': 13, 'hien_ngay': True}

# Ghi cân nặng cả đàn
requests.post(f"{URL}/api/lan-do", json={
    "dan": "D01", "thoi_gian": "2026-11-08T08:00:00",
    "ds": [{"con_id": "D01-03", "kg": 71.2, "anh": "recordings/con/D01-03.jpg"}]})

# Đọc vùng đã vẽ, dạng pixel của video 1920x1080
vung = requests.get(f"{URL}/api/o/A/vung",
                    params={"pixel": 1, "rong": 1920, "cao": 1080}).json()
```

### 8.5 Dùng vùng trong code
Cấu trúc (khoá nào chưa vẽ thì không có):

| Khoá | Nội dung | Dùng cho |
|---|---|---|
| `o` | Đa giác ô, `[[x,y], ...]` | Đếm lợn trong ô; PolygonZone |
| `mang_an` | Danh sách đa giác máng ăn | Module bỏ ăn |
| `lac_chuong` | `{"kieu":"vung","diem":[...]}` hoặc `{"kieu":"vach","diem":[p1,p2],"diem_ngoai":p}` | Sổng chuồng |
| `vat_tham_chieu` | `{"diem":[p1,p2],"cm":80}`; dạng pixel có thêm `cm_moi_pixel` | Đổi pixel sang cm cho cân nặng |

Xác định phía ngoài của vạch: lấy dấu của tích có hướng `(p2 - p1) × (điểm - p1)`; lợn ở phía ngoài khi dấu giống dấu của `diem_ngoai`. "Ra hẳn" nên hiểu là cả 4 góc hộp bao nằm ở phía ngoài.

## 9. Tham chiếu API

Mọi API trả JSON. Lỗi dạng `{"ok": false, "loi": ["..."]}`.

### 9.1 Sự kiện
**`POST /api/su-kien`** gửi sự kiện.

| Trường | Bắt buộc | Ghi chú |
|---|---|---|
| `loai` | Có | Một trong 9 loại ở mục 8.2 |
| `o` | Có | Mã ô, phải tồn tại |
| `thoi_gian` | Có | ISO 8601 |
| `muc` | Có | `khan_cap`, `canh_bao`, `thong_tin` |
| `anh` | Không | Đường dẫn tương đối dưới `data/` |
| `du_lieu` | Không | Object JSON |

Trả về `201 {"ok": true, "id": 13, "hien_ngay": true}`, hoặc `400` kèm lý do (thiếu trường, giá trị không hợp lệ, ô chưa có).

**`GET /api/su-kien`** 100 sự kiện mới nhất.

**`POST /api/su-kien/<id>/phan-hoi`** body `{"phan_hoi": "dung"}` hoặc `"bao_nham"`. Trả `{"ok": true, "trang_thai": "dung"}`; 400 nếu giá trị sai, 404 nếu không có sự kiện.

**`GET /api/thong-bao?sau=<id>`** dành cho banner. Trả `{"moi_nhat": N, "ds": [...]}` gồm các sự kiện hiện-ngay có mã lớn hơn `id`. Không truyền `sau` thì chỉ trả `moi_nhat`.

### 9.2 Cài đặt
**`GET /api/cai-dat`** trả toàn bộ cài đặt.
**`PUT /api/cai-dat`** có thể gửi từng phần:

```json
{
  "gio_canh_gac": {"bat": true, "tu": "20:00", "den": "05:00"},
  "gio_dem": {"tu": "07:00", "phut": 15},
  "gio_cho_an": ["06:30", "11:30", "17:00"],
  "nguong": {"lac_chuong_giay": 5, "coi_phan_tram": 15}
}
```
Sai định dạng trả 400 kèm lý do.

### 9.3 Ô chuồng và vùng
- **`GET /api/o/<ma>/vung`** vùng tỉ lệ 0 đến 1; thêm `?pixel=1&rong=<px>&cao=<px>` để lấy pixel.
- **`PUT /api/o/<ma>/vung`** lưu vùng (kiểm tra: đa giác ≥ 3 điểm, toạ độ trong 0 đến 1, vật tham chiếu cm > 0).
- **`POST /api/o/<ma>/anh-camera`** multipart, trường `file`: ảnh (jpg, jpeg, png) hoặc video (mp4, avi, mov, mkv). Sai định dạng trả 400.

### 9.4 Đàn và cân nặng
**`POST /api/lan-do`**

```json
{"dan": "D01", "thoi_gian": "2026-11-08T08:00:00",
 "ds": [{"con_id": "D01-03", "kg": 71.2, "anh": null}]}
```
`kg` trong khoảng 1 đến 400. Trả `201 {"ok": true, "so_con": 1}`.

**`GET /api/dan/<ma>/bao-cao`** các trường chính: `tb_kg`, `moc_kg`, `tb_chenh_moc`, `tang_kg`, `tang_pct`, `tang_kg_ngay`, `dong_deu_pct`, `cv_pct`, `tuoi_ngay`, `con_coi[]`, `con_lon_nhanh[]` (mỗi con: `con_id`, `anh`, `kg`, `chenh_moc`, `chenh_tb`, `chenh_tb_pct`), `chuoi[]` (trung bình và mốc theo ngày). Đàn chưa có lần đo: `co_du_lieu` là false.

### 9.5 Chạy video
- **`POST /api/chay-video`** multipart, trường `video` (file) và `o` (mã ô). Trả `202 {"ok": true, "job": "ab12cd34"}`.
- **`GET /api/chay-video/<job>`** trả `trang_thai` (`dang_chay`, `xong`, `loi`), `tien_do` (0 đến 1), `che_do` (`mock` hoặc `pipeline`), `ds` (sự kiện đã phát ra), `loi`.

Video tối đa 500 MB.

## 10. Chạy video qua pipeline

Trang: **Cài đặt → Chạy video demo**. Chọn ô, chọn video, bấm **Tải lên và chạy**; tiến độ và sự kiện hiện ngay trên trang, sự kiện cũng vào danh sách chung và có thể kích hoạt banner.

### Hợp đồng với pipeline (cần chốt với Nam)
Webapp tìm `ai/pipeline.py` và gọi:

```python
def chay_video(nguon, o, vung, on_event, tien_do=None):
    """
    nguon    : đường dẫn file video
    o        : mã ô chuồng, ví dụ "A"
    vung     : dict vùng theo PIXEL của video (xem mục 8.5)
    on_event : hàm nhận 1 dict sự kiện đúng định dạng mục 8.2;
               webapp tự lưu và quyết định banner
    tien_do  : hàm tuỳ chọn tien_do(0.0 .. 1.0)
    """
```
Ảnh khoanh đỏ lưu dưới `data/recordings/su_kien/`, trường `anh` ghi `recordings/su_kien/<tên>.jpg`.

### Chế độ MOCK (khi chưa có pipeline)
Trang hiện khung cam "Chế độ MOCK" và phát vài sự kiện mẫu. Tên file video chứa từ khoá nào thì phát loại tương ứng: `dem`, `nguoi`, `lac`, `ngu`, `an`. Không có từ khoá thì phát 2 sự kiện ngẫu nhiên. Sự kiện mẫu có `du_lieu.mock = true`.

Khi `ai/pipeline.py` import được, trang tự dùng pipeline thật, không cần sửa gì.

## 11. Quay video demo

Chuẩn bị:
1. `python seed.py`, rồi `python app.py`.
2. Vào Vẽ vùng, vẽ sẵn ô A (ô chuồng và vạch lạc chuồng).
3. Mở trình duyệt khung hẹp (khoảng 420 px).
4. Cửa sổ thứ hai: `python demo.py`; bấm Enter đúng lúc bắt đầu quay. Thử trước bằng `python demo.py --nhanh` (nhanh gấp 10).

Script phát 8 sự kiện theo mốc 10, 25, 45, 65, 80, 95, 105, 115 giây. Hai sự kiện người lạ và nghi trộm dùng giờ giả lập 23:30 để lọt giờ canh gác. Kịch bản chi tiết từng mốc, lời dẫn và thao tác: `docs/kich_ban_demo.md`.

Thử nhanh một sự kiện lẻ: `python simulate.py lac_chuong` (các loại: `nghi_trom`, `lac_chuong`, `nghi_chet`, `dem_thieu`, `tho_nhanh`, `bo_an`, `nguoi_la`, `dem_du`), hoặc `python simulate.py --lien tuc` để cứ 5 giây gửi một sự kiện.

## 12. Kiểm thử

```bash
python kiem_thu.py
```
Chạy trên cơ sở dữ liệu tạm nên không đụng dữ liệu thật. Gồm 29 mục: 10 trang mở được; nhận đủ 8 loại sự kiện; quy tắc banner (kể cả `nguoi_la` ban ngày và ban đêm); từ chối sự kiện sai; ghi lần đo và báo cáo; lưu và đọc vùng; chạy video. Kết thúc in `TẤT CẢ ĐẠT` hoặc danh sách lỗi (mã thoát 1). Nên chạy lại mỗi khi có mô-đun mới nối vào.

## 13. Xử lý sự cố

| Hiện tượng | Nguyên nhân và cách xử lý |
|---|---|
| Gửi sự kiện báo 400 "Ô 'X' chưa có trong hệ thống" | Mã ô không khớp. Xem danh sách ô ở trang Ô chuồng (mặc định A, B, C, D) |
| Gửi sự kiện báo 400 về `thoi_gian` | Phải là ISO, ví dụ `2026-11-10T02:14:00` |
| Sự kiện có nhưng không hiện banner | Có thể đúng quy tắc: mức `thong_tin` chỉ lưu; `nguoi_la` ngoài giờ canh gác chỉ lưu. Xem mục 6 |
| Banner không hiện sau khi gửi | Banner chỉ hiện sự kiện đến sau khi trang đã mở. Mở trang trước, rồi mới gửi |
| Ảnh sự kiện bị vỡ | `anh` phải là đường dẫn tương đối dưới `data/` (ví dụ `recordings/su_kien/x.jpg`) và file phải tồn tại |
| Vẽ vùng không có ảnh nền | Tải ảnh hoặc video ở phần "Ảnh nền" của trang vẽ |
| Tải video bị từ chối hoặc báo "Không đọc được video" | Video tối đa 500 MB và phải mở được bằng OpenCV (nên dùng mp4 H.264). Làm ảnh nền ở trang vẽ vùng chỉ nhận ảnh jpg, png hoặc video mp4, avi, mov, mkv |
| "Address already in use" khi chạy | Cổng 5000 đang bận: tắt tiến trình cũ hoặc chạy `flask --app app run --port 5001` |
| Mất hết dữ liệu | `seed.py` xoá và tạo lại cơ sở dữ liệu. Muốn giữ, sao lưu `data/trang_trai.db` trước |
| Điện thoại không vào được | Chạy với `--host 0.0.0.0`, cùng mạng Wi-Fi, và cho phép cổng 5000 qua tường lửa |
| Chạy video chỉ ra sự kiện mẫu, chữ MOCK | Chưa có `ai/pipeline.py` import được. Xem mục 10 |
| Lệnh `python` không tìm thấy thư viện | Chạy `pip install -r requirements.txt` trong đúng môi trường Python |

Ghi chú về phạm vi: webapp chạy máy chủ phát triển của Flask, không có đăng nhập, phục vụ một trang trại; phù hợp cho đồ án và demo, chưa phải cấu hình triển khai thật.
