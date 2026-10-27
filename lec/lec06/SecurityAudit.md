# Security Audit — Social Network API

## Phạm vi và trạng thái

Rà soát thiết kế cho POST /auth/login, POST /auth/refresh và GET /posts/{id} trong openapi.yaml.
Chưa có mã backend hoặc môi trường chạy để kiểm thử bảo mật thực tế.
Liệt kê ít nhất 5 điểm có thể lộ thông tin.

## Quyền và mã phản hồi

| Endpoint | Xác thực và scope | Thành công | Lỗi ứng dụng |
| --- | --- | --- | --- |
| POST /auth/login | Không cần token/scope; kiểm tra username/password | 200 | 400, 401, 415, 429, 500 |
| POST /auth/refresh | Không cần access token/scope; bắt buộc refresh token hợp lệ trong JSON body | 200 | 400, 401, 415, 429, 500 |
| GET /posts/{id} | Bearer access token và scope posts:read; kiểm tra thêm quyền trên bài viết | 200 | 400, 401, 403, 404, 429, 500 |

`400`: request sai cấu trúc.

`401`: không xác thực được

`403`: token hợp lệ nhưng thiếu scope

`404`: bài không tồn tại hoặc không được phép xem

`415`: sai Content-Type

`429`: vượt giới hạn

`500`: lỗi nội bộ.


Đây là API đăng nhập tùy chỉnh, không phải OAuth2 token endpoint. Các challenge Login/RefreshToken trong spec là quy ước riêng của API; frontend xử lý JSON lỗi và không trông chờ trình duyệt tự hiện hộp thoại đăng nhập.

## Các nguy cơ và biện pháp

| # | Vị trí / nguy cơ | Thông tin có thể lộ / tác động | Biện pháp | Cách kiểm thử dự kiến |
| --- | --- | --- | --- | --- |
| 1 | Login trả lỗi khác nhau cho tài khoản không tồn tại và sai mật khẩu | Danh sách username hợp lệ | Dùng cùng 401 và INVALID_CREDENTIALS; hạn chế chênh lệch thời gian xử lý, dùng phép kiểm tra hash giả khi user không tồn tại | So sánh status/body và phân bố thời gian của hai trường hợp; không kỳ vọng mọi request có thời gian giống hệt |
| 2 | Log request body hoặc Authorization | Mật khẩu, access token, refresh token có thể bị dùng để chiếm tài khoản | Che trường nhạy cảm ở proxy, ứng dụng, APM và log lỗi; không đưa token vào URL | Gửi thông tin thử nghiệm có marker rồi tìm marker trong log; không dùng thông tin thật |
| 3 | GET /posts/{id} chỉ kiểm tra token/scope, bỏ quyền trên đối tượng (BOLA/IDOR) | Nội dung bài private hoặc friends của người khác | Kiểm tra tác giả, visibility và quan hệ bạn bè trên server; từ chối mặc định | A tạo bài private; B có posts:read yêu cầu ID đó phải nhận 404; tác giả nhận 200 |
| 4 | Trả nguyên bản ghi database | Password hash, email riêng tư, metadata nội bộ hoặc trường quản trị | Serialize bằng allowlist đúng schema Post; không trả nguyên ORM object | Kiểm tra response chỉ chứa id, author_id, content, visibility, created_at |
| 5 | Refresh token dùng lại được hoặc lưu plaintext | Token bị đánh cắp có thể duy trì quyền truy cập lâu dài | Token ngẫu nhiên đủ mạnh; lưu hash; rotation nguyên tử; phát hiện reuse và thu hồi family; có thời hạn | Dùng R1 lấy R2, dùng lại R1 phải thất bại; R2 sau sự kiện reuse cũng phải bị từ chối; thử refresh đồng thời |
| 6 | JWT xác minh không đầy đủ | Giả mạo danh tính hoặc quyền đọc bài viết | Allowlist thuật toán; kiểm tra chữ ký, exp, iss, aud, sub; kiểm tra scope ở server; không chỉ decode JWT | Sửa payload, dùng token hết hạn, sai issuer/audience hoặc chữ ký: 401; token hợp lệ thiếu posts:read: 403 |
| 7 | HTTP hoặc cache phản hồi nhạy cảm | Mật khẩu/token/nội dung riêng tư lộ trên đường truyền hoặc cache dùng chung | Chỉ HTTPS; HSTS tại triển khai phù hợp; Cache-Control: no-store cho token và bài viết; không đưa bí mật vào query string | Kiểm tra HTTPS và header; xác minh proxy không cache token hoặc trả nội dung của A cho B |
| 8 | Không giới hạn login/refresh | Dò mật khẩu, chiếm tài khoản, cạn tài nguyên | Rate limit theo IP kết hợp tài khoản/phiên; phản hồi 429 với Retry-After; không chỉ dựa vào IP | Vượt ngưỡng cấu hình và kiểm tra 429; thử nhiều IP/tài khoản theo kịch bản kiểm thử được phép |
| 9 | Commit secret hoặc token mẫu thật | JWT signing key, mật khẩu DB, tài khoản người dùng | Secret manager/biến môi trường; ignore .env; chỉ dùng dữ liệu giả; secret scanning; nếu đã lộ phải thu hồi/đổi secret | Rà soát staged diff và lịch sử commit trước khi push |
