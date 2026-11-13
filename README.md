# TV4 — Bảo Nguyên | Bộ triển khai tuần 1–2, phiên bản 2.0

ĐỌC TRƯỚC: Đây là mã nguồn và tài liệu hoàn thiện trong phạm vi TV4. Không phải mô hình
đã train hoặc toàn bộ hệ thống trang trại đã tích hợp. Kết quả demo được tạo từ bbox giả lập,
KHÔNG phải kết quả YOLO, không được dùng làm số liệu AP hoặc precision/recall thực tế.
Gói này thay thế bản TV4_Tuan1_Tuan2 cũ. Giải nén thư mục riêng, không chép đè TV4 hiện có.
Chưa nhận mã nguồn TV4 trong ảnh nên chưa kiểm tra tương thích với mã nguồn đó.

## 1. Chạy ngay trên Mac/Windows/Linux
Mở terminal tại thư mục chứa README này, không phải thư mục cha.
Python đề xuất: 3.11. Cài mới hoặc dùng venv sạch; không sao chép .venv từ máy khác.
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m scripts.doctor
python -m unittest discover -s tests -v
python -m scripts.replay --config examples/demo_config.json --frames examples/frames.jsonl --out runs/demo_new
```
Windows dùng `python` thay `python3` và kích hoạt bằng `.venv\Scripts\activate`.
Kỳ vọng demo: 1 lac_chuong tại giây 8 và 1 dem_thieu sau đếm lại. Xem events.jsonl,
count_summary.json và evidence/ (bbox đỏ). Lệnh replay không train, không cần GPU/torch.
Dùng out mới mỗi lần; events.jsonl là append-only, chạy lại cùng out sẽ có sự kiện trùng.

## 2. Môi trường train
Cài PyTorch theo nền tảng/CUDA/driver từ hướng dẫn chính thức của PyTorch rồi:
```bash
python -m pip install -r requirements-train.txt
python -m scripts.doctor
```
GPU NVIDIA: device 0. Apple Silicon: thử --device mps khi doctor báo khả dụng;
Mac Intel: --device cpu. MPS/CPU không được cam kết hiệu năng/tương thích như CUDA.
Train chính nên chạy trên GPU CUDA; không đặt device 0 trên Mac không có CUDA.
Torch/Ultralytics có thể tải model pretrained từ Internet lần đầu; dữ liệu vẫn do TV1 bàn giao.
Không cài lẫn opencv-python và opencv-python-headless trong cùng môi trường.

## 3. Tuần 1 — dữ liệu, baseline và smoke test
Sửa `config/data.yaml`, path tuyệt đối đến bộ YOLO đã xử lý:
images/train, images/val, images/test và labels/train, labels/val, labels/test.
Các đường dẫn split là thư mục, không phải danh sách trong chế độ audit.
Class 0=pig; một txt cùng đường dẫn tương đối cho mỗi ảnh. Giữ split gốc PigDetect.
```bash
python -m scripts.data_tools audit --data config/data.yaml --out reports/data
python -m scripts.data_tools visualize --data config/data.yaml --out reports/labels
python -m scripts.train --config config/train.yaml --smoke --device mps --batch 2
python -m scripts.train --config config/train.yaml --device mps --batch 8
```
Smoke: 1 epoch trên dữ liệu thật; không thay cho baseline 100 epochs. Audit không tự sửa nhãn.
Ảnh âm phải có txt rỗng đã xác nhận. Audit phát hiện trùng nội dung, không chứng minh hết
rò rỉ theo chuồng/video; cần metadata từ TV1 để đối chiếu split và chuỗi gần nhau.
Nếu OOM giảm batch; chỉ đổi model khi ghi lý do và đo lại. Seed hỗ trợ tái lập, không bảo đảm
bitwise giống nhau giữa mọi phiên bản/phần cứng.

## 4. Tuần 2 — phân tích, chọn và đánh giá cuối
```bash
python -m scripts.train --resume runs/detect/pig_set_baseline/weights/last.pt
python -m scripts.evaluate --weights runs/detect/pig_set_baseline/weights/best.pt --split val --device mps
python -m scripts.analyze --csv runs/detect/pig_set_baseline/results.csv --out reports/training
# Chốt cấu hình bằng validation trước khi chạy test:
python -m scripts.evaluate --weights runs/detect/pig_set_baseline/weights/best.pt --split test --device mps
python -m scripts.package_model --weights runs/detect/pig_set_baseline/weights/best.pt --metrics runs/evaluation/test/metrics.json --out models/handover
```
Resume lấy cấu hình từ checkpoint; không dùng để thay đổi tùy tiện thí nghiệm cũ.
Ultralytics có thể tăng hậu tố đường dẫn khi output tồn tại; phải dùng đường dẫn thật.
AP >=80 chưa rõ IoU trong phân công: báo cả mAP50/mAP50-95 và xác nhận với nhóm,
không tự coi AP50=80 là đạt AP50-95=80. Detection không có một classification accuracy thay mAP.
Không chọn cấu hình bằng test. Đường cong validation không phải kết quả test.
Package kiểm tra SHA256 checkpoint khớp metrics và split=test, nhưng không chứng minh
metrics không bị người dùng sửa; giữ nguyên log gốc để truy xuất.

## 5. Ngày/đêm và lỗi
Tạo CSV metadata có cột image,lighting; image tương đối với data root và lighting=day/night.
Phải phủ đúng toàn bộ test, không trùng, không tự đoán nhãn đêm bằng độ sáng.
```bash
python -m scripts.subsets --data config/data.yaml --metadata path/to/test_metadata.csv --out reports/subsets
python -m scripts.evaluate --weights models/handover/pig_set.pt --data reports/subsets/day.yaml --split test --out runs/evaluation_day --device mps
python -m scripts.evaluate --weights models/handover/pig_set.pt --data reports/subsets/night.yaml --split test --out runs/evaluation_night --device mps
```
Đây là phân tích phân nhóm sau khi chốt model, không dùng để tối ưu trên test.
Ultralytics val xuất đồ thị/ảnh minh họa; review thủ công ảnh bỏ sót/dư và ghi trong
`reports/ERROR_REVIEW_TEMPLATE.csv`. Chưa có auto-mining mọi false positive/negative.

## 6. Video thật — chuẩn bị tuần 3
```bash
python -m scripts.video --weights models/handover/pig_set.pt --source path/to/demo.mp4 --config config/pen.json --out runs/video_new --device cpu --start-time 2026-11-06T08:00:00+07:00
```
Sửa polygon, size, registered theo video; từ chối kích thước sai. Timestamp dùng index/fps
(giả định video CFR). Video VFR/camera trực tiếp phải dùng adapter timestamp thật của TV2.
Không tự resize ảnh mà giữ polygon cũ. Không nhận luồng RTSP trong CLI này.
Count mặc định 900 giây + recount 120 giây; video ngắn hơn ghi trạng thái incomplete,
không bịa kết luận. Demo dùng 10+6 giây chỉ để test. Bbox clipping/ID có sẵn do Ultralytics.
Không có track ID vẫn đếm detection, nhưng không kích hoạt escape theo cá thể.

## 7. Logic nghiệp vụ
- Đếm: mẫu đầu tiên mỗi giây video. Max của min trong các cửa sổ 5 mẫu liên tục.
  Gap reset cửa sổ. Coverage <80% hoặc không đủ cửa sổ => insufficient_data, không phát dem_du.
  Thiếu lượt đầu -> recount. Thiếu cả hai -> dem_thieu. Dư -> overcount_review, không dem_du.
- Bbox thuộc ô khi tâm trong polygon, kể cả biên. Sổng khi toàn bbox không chạm/giao polygon.
  Polygon phải đơn, không đóng lặp đỉnh; đã có kiểm tra tự cắt và biên ảnh.
- Escape: cùng ID ngoài ô >=5 giây, gap >1 giây reset. Cooldown=300 giây, cấu hình pen/track.
  Mặc định pen giúp chống spam do ID switch nhưng có thể gộp hai con thoát trong cùng ô.
- Chỉ dùng cho camera/ô có ownership rõ. Nếu thấy nhiều ô, TV2 cần cấp owned_track_ids hoặc
  phân công track theo lịch sử; không gọi mọi con ngoài ô A là lợn của A.
- Tạo ảnh bằng chứng trước khi phát event, ảnh lỗi sẽ raise, không âm thầm gửi event thiếu ảnh.
  Engine ghi JSONL; TV3 quyết định ghi DB/hiển thị, không có HTTP/DB trong module TV4.
- Một Engine/phiên/camera/ô; không dùng chung thread, không khôi phục cooldown sau restart.
  Đếm được khởi động khi tạo Engine; lịch chạy do pipeline/scheduler TV2 điều khiển.

## 8. Đánh giá nghiệp vụ
```bash
python -m scripts.evaluate_business --truth examples/truth_events.json --pred examples/pred_events.json --counts examples/counts.csv --out reports/demo_metrics.json
```
Đây là fixture giả lập. Đầu vào event_metrics là JSON array {pen,kind,t}, t là thời điểm
cảnh báo kỳ vọng (qua biên + hold), không phải thời điểm bắt đầu thoát.
Ghép một-một theo cùng pen/kind trong tolerance; không đếm hai cảnh báo trùng thành hai TP.
Trường hợp không có mẫu/positive, metric null thay vì khẳng định 100%.

## 9. Kiểm thử và phạm vi đã kiểm chứng
Xem reports/TEST_RESULTS.txt, CLI_TEST_RESULTS.json, RELEASE_VERIFICATION.json.
Đã chạy core unit/integration, replay JSONL, tạo ảnh bằng chứng và phân tích CSV giả lập.
Chưa train PigDetect, chưa chạy YOLO inference thật/CUDA/MPS/camera/WebDB.
Không kèm dữ liệu gốc, pig_set.pt giả hoặc số liệu AP. Dependencies ML chỉ import khi dùng.
Kiểm thử trên Python thực tế ghi trong report; chưa chạy trực tiếp trên máy Mac của bạn.

## 10. Tài liệu và nguồn
`docs/Bao_cao_TV4_Tuan1_Tuan2.docx`: báo cáo Word chi tiết.
`docs/TRACEABILITY.csv`: yêu cầu → triển khai → kiểm thử → trạng thái.
`docs/INTEGRATION.md`: hợp đồng TV2/TV3. `notebooks/Training_Workflow.ipynb`: lệnh train.
Nguồn chính là hai file DOCX do người dùng cung cấp, ưu tiên bản phân công cập nhật.
Không sao chép notebook outputs giả thành kết quả thật. Không tải checkpoint không tin cậy.

## Mac M5 / dataset-ready v3
Read [OPTIMIZATION_M5_V3.md](OPTIMIZATION_M5_V3.md) first. Run `python -m scripts.preflight` before training to validate the actual YOLO dataset and runtime.
