# Kịch bản video demo webapp (2 phút)

## Chuẩn bị (làm trước khi quay)
1. `python seed.py` (dữ liệu sạch) rồi `python app.py`.
2. Vào **Vẽ vùng** và vẽ sẵn ô A (ô chuồng + vạch lạc chuồng) để cảnh vẽ vùng quay nhanh. Nếu có ảnh thật của trại, tải lên làm ảnh nền.
3. Mở trình duyệt khung hẹp (~420 px) hoặc DevTools chế độ điện thoại. Quay ở Trang chủ.
4. Cửa sổ thứ hai chạy `python demo.py`, **bấm Enter đúng lúc bắt đầu quay**; script tự phát sự kiện theo mốc bên dưới. Thử trước bằng `python demo.py --nhanh`.
5. Nếu Nam đã giao `ai/pipeline.py`: thay cảnh 1:55 bằng chạy video thật ở trang **Chạy video**.

## Dòng thời gian
| Mốc | Màn hình | Lời dẫn gợi ý | Thao tác |
|---|---|---|---|
| 0:00–0:10 | Trang chủ | Hệ thống giám sát trang trại lợn bằng camera, xem như app điện thoại. | Cuộn nhẹ: tổng số lợn, các ô, sự kiện gần đây. |
| 0:10 | (tự phát) `dem_du` ô A | Đếm đủ là thông tin, chỉ lưu, không làm phiền chủ trại. | Không có banner. Mở tab **Sự kiện** cho thấy mục mới. |
| 0:25 | Banner `dem_thieu` ô C | Đếm thiếu 2 con: cảnh báo kèm ảnh khung đếm được nhiều nhất. | Bấm **Đúng**. |
| 0:45 | Banner `lac_chuong` ô B (khẩn cấp) | Lợn ra khỏi vạch quá 5 giây, báo ngay kèm ảnh khoanh đỏ. | Bấm **Báo nhầm**, nói rõ hệ thống ghi nhận để chỉnh ngưỡng. |
| 1:05 | Banner `nguoi_la` ô A | Ban đêm trong giờ canh gác, người lạ được báo ngay. | Mở **Cài đặt**, chỉ giờ canh gác 20:00–05:00. |
| 1:20 | Banner `nghi_trom` ô A | Nghi trộm luôn khẩn cấp, bật tắt canh gác không ảnh hưởng việc phát hiện người. | Bấm **Đúng**. |
| 1:30 | **Vẽ vùng** ô A | Chủ trại tự vẽ ô, máng ăn, vạch lạc chuồng và vật tham chiếu trên ảnh camera. | Vẽ nhanh một vùng, bấm Lưu. |
| 1:45 | Banner `tho_nhanh` ô D, `bo_an` ô B | Sức khỏe: thở nhanh và bỏ ăn là cảnh báo sớm. | Để banner xếp hàng "+1", bấm Đúng lần lượt. |
| 1:50 | **Đàn** → Đàn D01 | Báo cáo phát triển: trung bình đàn, tăng kg, độ đồng đều, con còi, con lớn nhanh. | Mở tab Con còi, chỉ chênh so với mốc và trung bình đàn. |
| 1:55 | Banner `nghi_chet` ô D | Nghi chết: khẩn cấp, luôn hiện ngay. | Kết, quay về Trang chủ, chấm đỏ cạnh ô có khẩn cấp. |

Lưu ý: tổng 2 phút rất sát; nếu thừa thời gian ở cảnh Đàn, bỏ cảnh Vẽ vùng ra một đoạn riêng hoặc quay 2 video rồi ghép.
Cảnh `nguoi_la` và `nghi_trom` dùng giờ giả lập 23:30 để lọt giờ canh gác; nói rõ đây là cảnh mô phỏng nếu thầy cô hỏi.
