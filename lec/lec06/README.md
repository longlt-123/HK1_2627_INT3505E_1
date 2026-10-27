# Social Network API — OpenAPI Specification

Tài liệu đặc tả API mạng xã hội theo **OpenAPI 3.0.3**, phiên bản API **1.0.0**. File [openapi.yaml](./openapi.yaml) mô tả cấu trúc request/response, yêu cầu xác thực, scope và mã lỗi của ba endpoint đăng nhập, làm mới token và xem bài viết.

Bản rà soát các nguy cơ lộ thông tin, biện pháp khắc phục và cách kiểm thử dự kiến được trình bày trong **[SecurityAudit.md](./SecurityAudit.md)**.

## Các file trong bài nộp

| File | Nội dung |
| --- | --- |
| [openapi.yaml](./openapi.yaml) | Hợp đồng API: endpoint, schema, xác thực, quyền và phản hồi |
| [SecurityAudit.md](./SecurityAudit.md) | 9 nguy cơ bảo mật, tác động, biện pháp và cách kiểm thử dự kiến |
| README.md | Giới thiệu và hướng dẫn đọc đặc tả |

Đặt ba file trong cùng thư mục, sử dụng đúng tên `openapi.yaml` và `SecurityAudit.md` để các liên kết tương đối hoạt động trên repository.

## Tổng quan endpoint

| Method | Endpoint | Chức năng | Xác thực / scope | Status code |
| --- | --- | --- | --- | --- |
| POST | `/auth/login` | Đăng nhập, nhận access token và refresh token | Không cần token/scope trước khi đăng nhập; kiểm tra username/password | 200, 400, 401, 415, 429, 500 |
| POST | `/auth/refresh` | Đổi refresh token lấy cặp token mới | Không cần access token/scope; bắt buộc refresh token hợp lệ trong body | 200, 400, 401, 415, 429, 500 |
| GET | `/posts/{id}` | Xem bài viết theo ID | Bearer JWT, scope `posts:read` và quyền xem bài viết | 200, 400, 401, 403, 404, 429, 500 |


## 1. Đăng nhập — POST /auth/login

Request sử dụng `Content-Type: application/json` và hai trường bắt buộc:

```json
{
  "username": "demo_user",
  "password": "example_password"
}
```

Khi xác thực thành công, API trả `200` với schema `TokenPair`:

| Trường | Ý nghĩa |
| --- | --- |
| `access_token` | JWT dùng để gọi API được bảo vệ |
| `refresh_token` | Token dùng để lấy cặp token mới |
| `token_type` | Luôn là `Bearer` |
| `expires_in` | Thời hạn access token: 900 giây (15 phút) |
| `refresh_expires_in` | Thời hạn refresh token: 604800 giây (7 ngày) |
| `scope` | Các quyền do server cấp, cách nhau bằng dấu cách; có thể rỗng |

Tài khoản không tồn tại, sai mật khẩu hoặc bị vô hiệu hóa đều trả cùng lỗi `401`, tránh tiết lộ sự tồn tại của tài khoản. Client không được tự gán scope trong request đăng nhập.

## 2. Làm mới token — POST /auth/refresh

Request sử dụng `Content-Type: application/json`:

```json
{
  "refresh_token": "<refresh_token_da_nhan>"
}
```
Endpoint không yêu cầu Bearer access token ở header nhưng vẫn phải xác minh refresh token trong body.

Đặc tả quy định **refresh token rotation**:

1. Server kiểm tra refresh token, phiên và tài khoản.
2. Nếu hợp lệ, vô hiệu hóa token cũ và cấp cặp token mới trong một giao dịch nguyên tử.
3. Client lưu token mới cho lần sử dụng tiếp theo.
4. Nếu phát hiện token cũ bị dùng lại, thu hồi toàn bộ nhóm refresh token thuộc phiên đó và trả `401`.

Refresh token là chuỗi opaque ngẫu nhiên; phía server chỉ lưu hash. Scope mới không được vượt quá quyền đã cấp ban đầu và quyền hiện tại của tài khoản. Client cần tránh gửi đồng thời nhiều request refresh.

Việc thu hồi refresh token không mặc nhiên làm JWT access token mất hiệu lực ngay. Nếu chưa có cơ chế thu hồi tức thời, access token đã cấp có thể còn hiệu lực đến khi hết hạn.

## 3. Xem bài viết — GET /posts/{id}

`id` là số nguyên dương. Request phải có header:

```http
Authorization: Bearer <access_token>
```

Server kiểm tra xác thực, tiếp đến scope `posts:read`, rồi quyền xem bài viết. Yêu cầu token và scope áp dụng cả với bài `public`.

| Visibility | Người được xem sau khi đáp ứng yêu cầu token/scope |
| --- | --- |
| `public` | Mọi người dùng đã xác thực có scope |
| `friends` | Tác giả hoặc bạn bè đã được chấp nhận |
| `private` | Chỉ tác giả |

Scope `posts:read` không cho phép đọc tất cả bài riêng tư. Bài không tồn tại và bài người gọi không được phép xem đều trả cùng `404` để hạn chế dò ID.

Ví dụ response `200` theo spec:

```json
{
  "id": 42,
  "author_id": 7,
  "content": "Xin chào!",
  "visibility": "public",
  "created_at": "2026-10-27T08:00:00Z"
}
```

## Cấu trúc file openapi.yaml

| Thành phần | Vai trò |
| --- | --- |
| `openapi` | Phiên bản chuẩn đặc tả: 3.0.3 |
| `info` | Tên, phiên bản và mô tả API |
| `servers` | URL server |
| `paths` | Ba endpoint, request, quyền và response tương ứng |
| `components.securitySchemes` | Khai báo cơ chế `BearerAuth` dùng HTTP Bearer JWT |
| `components.schemas` | Schema dùng chung: `LoginRequest`, `RefreshRequest`, `TokenPair`, `Error`, `Post` |
| `components.responses` | Phản hồi dùng lại, được tham chiếu bằng `$ref` |

Các object schema đều có:
- `additionalProperties: false`, tức không chấp nhận trường ngoài danh sách đã khai báo. 
- `required` chỉ ra các trường bắt buộc.
- `writeOnly: true` trên mật khẩu/refresh token. (trong request là mô tả schema, không tự mã hóa hoặc che dữ liệu trong log)

Trong `security`, `BearerAuth: []` thể hiện yêu cầu Bearer token. Với HTTP Bearer, mảng này để rỗng; yêu cầu scope được ghi riêng bằng extension `x-required-scopes: [posts:read]` và mô tả endpoint. Backend phải thực hiện kiểm tra scope.

`security: []` bỏ yêu cầu Bearer ở header; không bỏ việc kiểm tra username/password hoặc refresh token.

## Mã lỗi và header

Response lỗi có hai trường bắt buộc `code` và `message`:

```json
{
  "code": "INSUFFICIENT_SCOPE",
  "message": "Access token hợp lệ nhưng không có scope posts:read."
}
```

| HTTP status | Mã lỗi trong body | Ý nghĩa |
| --- | --- | --- |
| 400 | `INVALID_REQUEST` | JSON không hợp lệ, thiếu trường hoặc sai schema |
| 401 | `INVALID_CREDENTIALS` | Không xác thực được thông tin đăng nhập |
| 401 | `INVALID_REFRESH_TOKEN` | Refresh token không hợp lệ, hết hạn, bị thu hồi hoặc đã dùng |
| 401 | `INVALID_ACCESS_TOKEN` | Thiếu access token hoặc access token không hợp lệ |
| 403 | `INSUFFICIENT_SCOPE` | Access token hợp lệ nhưng thiếu `posts:read` |
| 404 | `POST_NOT_FOUND` | Bài không tồn tại hoặc người gọi không được phép xem |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | Body phải dùng `application/json` |
| 429 | `RATE_LIMITED` | Vượt giới hạn số request |
| 500 | `INTERNAL_ERROR` | Lỗi nội bộ; không trả chi tiết hệ thống |

Các mã chuỗi trên được mô tả trong ví dụ response.

Các header được mô tả trong spec:

- `Cache-Control: no-store`: có trên phản hồi token, bài viết và các lỗi đã khai báo.
- `Pragma: no-cache`: bổ sung trên phản hồi cấp token.
- `WWW-Authenticate`: có trên lỗi `401`, tương ứng cơ chế xác thực của endpoint.
- `Retry-After`: số giây cần chờ trước khi thử lại sau lỗi `429`.

Theo [SecurityAudit.md](./SecurityAudit.md), đây là API đăng nhập tùy chỉnh, không phải OAuth2 token endpoint. Các challenge `Login` và `RefreshToken` là quy ước riêng của API.

## Phạm vi bảo mật

[SecurityAudit.md](./SecurityAudit.md) trình bày 9 nguy cơ: dò tài khoản qua lỗi đăng nhập; lộ credential trong log; bỏ kiểm tra quyền trên bài viết; trả dư trường database; refresh token bị dùng lại hoặc lưu plaintext; xác minh JWT không đầy đủ; truyền HTTP hoặc cache dữ liệu nhạy cảm; thiếu giới hạn request; và commit secret vào repository.
