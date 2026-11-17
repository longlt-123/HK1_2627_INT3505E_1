# Lab 4 — Phân tích kết quả Locust

## Kết quả đo

Nguồn chính là số liệu của [A.html](../reports/A.html), [B.html](../reports/B.html), [C.html](../reports/C.html). CSV và log được giữ để kiểm tra thêm; CSV ghi định kỳ có thể thiếu vài request cuối, ví dụ A CSV có 138 request trong khi HTML cuối lượt có 140.

Failure rate = số failure / số request × 100%. RPS dùng `total_rps`

| Kịch bản | Users | Spawn rate (user/s) | Duration cấu hình | Requests | p95 tổng (ms) | Failures | Failure rate tổng | RPS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 10 | 2 | 30s | 140 | 12 | 1 | 0,714% | 4,77 |
| B | 50 | 5 | 60s | 1396 | 12 | 2 | 0,143% | 23,43 |
| C | 200 | 50 | 30s | 2883 | 73 | 0 | 0,000% | 97,47 |

Chi tiết theo endpoint, mỗi ô ghi **p95 (ms); failures/requests**:

| Endpoint | A | B | C |
|---|---|---|---|
| GET /books | 7; 0/60 | 9; 0/577 | 61; 0/1264 |
| GET /books/{id} | 5; 0/41 | 7; 0/423 | 51; 0/785 |
| GET /books?year={year} | 5; 1/26 | 8; 2/190 | 85; 0/414 |
| POST /books | 250; 0/13 | 20; 0/206 | 130; 0/420 |

## 1. Kịch bản nào có p95 cao nhất? Vì sao?

Kịch bản C có p95 tổng cao nhất với 73 ms (gấp khoảng 6 lần mức 12 ms của A và B). Khi tăng từ 50 lên 200 users (từ B sang C), RPS tăng tương ứng khoảng 4,16 lần (từ 23,43 lên 97,47 req/s) cho thấy hệ thống chưa chạm trần throughput, nhưng độ trễ phần đuôi bắt đầu giãn rõ—đặc biệt ở GET /books?year={year} (8 → 85 ms) và POST /books (20 → 130 ms).

Các nguyên nhân khả dĩ (ở mức giả thuyết do bài đo chưa thu thập metric CPU, DB lock hay query plan):

- Tranh chấp tài nguyên: 200 user đồng thời làm tăng thời gian chờ luồng xử lý và kết nối DB.

- Chi phí ghi và truy vấn: POST /books phải gọi db.session.commit() để ghi xuống SQLite, trong khi GET /books?year={year} lọc trên cột Book.year chưa đánh index và kích thước dữ liệu tăng dần qua các lượt chạy.

Lưu ý ngoại lệ: Riêng POST /books ở kịch bản A có p95 lên tới 250 ms, nhưng đây chỉ là nhiễu do cỡ mẫu quá nhỏ (chỉ có 13 request POST, bị kéo lệch bởi một request mất ~246 ms), không phải do kịch bản A chịu tải kém hơn C.

## 2. Endpoint nào tăng failure rate theo số user?

**Không quan sát thấy endpoint nào có failure rate tăng theo số user trong ba lượt này.** Các lỗi ghi nhận đều thuộc tìm theo năm và đều là lỗi giả lập:

- A: 1/26 search = **3,846%**.
- B: 2/190 search = **1,053%**.
- C: 0/414 search = **0%**.

Chênh lệch do lấy mẫu ngẫu nhiên; không phải API tự phục hồi khi tăng tải. Với xác suất 1% mỗi search, xác suất không gặp lỗi giả lập trong 414 search là `0.99^414`, khoảng **1,56%**; kết quả C bằng 0 vẫn có thể xảy ra.

Không có failure ngoài giả lập hoặc exception được Locust ghi nhận. Vì GET theo ID chủ động chấp nhận 404, kết luận này không có nghĩa mọi HTTP response đều là 2xx.

## 3. SLO p95 < 300 ms và baseline CI

**Cả A, B, C đều đạt ngưỡng độ trễ p95 < 300 ms trong phép đo local này**, cả tổng hợp lẫn từng endpoint.

Đề xuất ban đầu cho CI (chưa triển khai gate tự động trong bài):

1. Dùng A: 10 users, spawn 2 user/s, 30 giây, database test riêng với dữ liệu cố định và server cùng cấu hình qua các lượt.
2. Đặt `$env:LOCUST_FAKE_FAILURE_RATE = '0'` để loại lỗi nhân tạo. Kiểm tra exit code và không có exception/failure ngoài các 404 đã định nghĩa là hợp lệ.
3. Gate p95 tổng **và mỗi endpoint < 300 ms**, failure rate thực **0%**. Không chỉ kiểm tra tổng vì có thể che endpoint chậm ít được gọi.
4. Trên cùng loại CI runner, dùng RPS khoảng **4 request/s** làm mức kiểm tra sơ bộ dựa trên A đạt 4,77; hiệu chỉnh sau nhiều lượt đo. RPS ở đây chịu ảnh hưởng thời gian nghỉ 1–3 giây, không biểu thị công suất tối đa.
5. Thu thêm mẫu bằng cách tăng thời gian đo, warm-up riêng và lặp lại trước khi dùng gate để chặn merge. B dùng cho regression dài hơn, C cho kiểm tra spike định kỳ. Không dùng con số một lượt làm chuẩn cố định cho mọi máy.

Giới hạn: cùng máy phát tải/chạy API, localhost không phản ánh độ trễ mạng, thời gian ngắn, không reset DB, không có warm-up riêng, dữ liệu nhỏ, có 404 được chấp nhận và chưa giám sát CPU/I/O. Flask development server + SQLite không chứng minh SLO production; cần đo lại trên cấu hình và workload đại diện cho production.

## Bonus: connection pool giới hạn 5 với 200 user

Để giới hạn cứng tối đa 5 kết nối trong SQLAlchemy QueuePool, cần cấu hình **`pool_size=5`, `max_overflow=0`** (nếu chỉ đặt `pool_size=5`, SQLAlchemy vẫn mở thêm kết nối overflow khi tải tăng). Khi 5 kết nối đều bận, các request tiếp theo sẽ phải xếp hàng chờ và chỉ lỗi (HTTP 500/timeout) nếu thời gian chờ vượt quá `pool_timeout`. Do đó, 200 user đồng thời không làm 195 request lỗi ngay lập tức vì mỗi user còn thời gian nghỉ 1–3s và các truy vấn nhẹ giải phóng kết nối khá nhanh.

Cách kiểm chứng đề xuất, **chưa chạy thí nghiệm giới hạn pool trong A/B/C**:

1. Tạo hai instance test với cùng snapshot DB, cùng worker và cùng máy; cấu hình engine trước `db.init_app()`. Một instance dùng pool 5, một dùng pool 20, đều `max_overflow=0`, cùng `pool_timeout` (ví dụ 5 giây). Không đổi nhiều yếu tố cùng lúc.
2. Tắt lỗi giả lập và chạy cùng kịch bản C cho từng instance, lưu báo cáo riêng. Nếu chưa gây chờ, tăng tải hoặc giảm wait time trong một workload thí nghiệm riêng, ghi rõ sự khác biệt.
3. So sánh p95/p99, RPS, HTTP 5xx và timeout. Đồng thời thu log server về QueuePool timeout, số kết nối checked-out và thời gian chờ lấy kết nối.
4. Locust chỉ thấy triệu chứng phía HTTP; cần log/metrics server để phân biệt nghẽn pool với SQLite lock, CPU hoặc giới hạn worker. Nếu p95 giảm và timeout biến mất khi tăng pool thì có bằng chứng hỗ trợ giả thuyết nghẽn pool; nếu không, điều tra nguyên nhân khác.

## File tổng hợp

[reports/lab4-submission.zip](../reports/lab4-submission.zip)
