# TV4 → TV2/TV3
TV1 cung cấp PigDetect YOLO đúng split. TV4 train detector và export trọng số/model card.
TV2 sở hữu pipeline chung, tracking BoT-SORT, lịch đếm, camera timestamp và phân ô/track.
TV3 sở hữu Flask/MySQL/thông báo, không thuộc gói này.
Frame: {t: giây video, wall_time: ISO8601 có offset, pen: mã ô, size:[W,H],
image: file ảnh tại frame đó, detections:[{bbox:[x1,y1,x2,y2],confidence:0..1,class_id:0,track_id:int|null}]}.
BBox pixel trong ảnh gốc; không normalized. Frame tăng thời gian nghiêm ngặt.
Engine.process(frame) trả list event đồng thời lưu JSONL, mỗi event có đúng 6 trường như phân công.
Sự kiện đếm có thể rỗng nếu chưa kết thúc; xem count_summary cho insufficient/overcount.
Ảnh count được chọn từ cửa sổ hỗ trợ mức ổn định, không nhất thiết là frame lúc kết luận.
Sự kiện escape có tracker_ids, video_seconds, hold_seconds. ID là ngắn hạn, không định danh lâu dài.
Không gửi lại JSONL trực tiếp lên DB mà không thiết kế idempotency ở phía pipeline.
Đề xuất ID chống trùng: camera/session/pen/type/video_second; thống nhất với TV3 trước tích hợp.
Cooldown theo ô hoặc track là lựa chọn cấu hình cần nhóm duyệt, không phải yêu cầu đã chốt.
