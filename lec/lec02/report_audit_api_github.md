# Báo cáo Audit Public API

**Đối tượng Audit:** GitHub REST API (v3)
**Base URL:** `https://api.github.com`

GitHub API là một trong những API công khai phổ biến nhất, được thiết kế bám sát các nguyên tắc của kiến trúc RESTful.

---

### 1. Lấy thông tin của một người dùng cụ thể

- **Endpoint:** `/users/{username}`
- **Method:** `GET`
- **Status Code:**
  - `200 OK`: Khi tìm thấy người dùng và trả về dữ liệu thành công.
  - `404 Not Found`: Khi không tìm thấy `{username}`.
- **Headers quan trọng:**
  - _Request:_ `Accept: application/vnd.github+json` (Khuyến nghị từ GitHub để chỉ định phiên bản API).
  - _Response:_ `Content-Type: application/json`.
- **Có RESTful không?**: **Có.** Thiết kế URL trỏ trực tiếp đến một tài nguyên cụ thể (một user trong tập hợp users) và sử dụng HTTP method `GET` chuẩn xác cho hành động đọc/truy xuất dữ liệu, không làm thay đổi trạng thái hệ thống.

---

### 2. Lấy danh sách Repositories của một người dùng

- **Endpoint:** `/users/{username}/repos`
- **Method:** `GET`
- **Status Code:**
  - `200 OK`: Trả về danh sách repository thành công.
  - `404 Not Found`: User không tồn tại.
- **Headers quan trọng:**
  - _Request:_ `Accept: application/vnd.github+json`
- **Có RESTful không?**: **Có.** Cấu trúc URL thể hiện rõ mối quan hệ phân cấp tài nguyên: `repos` là tập hợp con thuộc về một cá thể trong tập hợp `users`. Sử dụng `GET` để truy xuất là hoàn toàn chuẩn REST.

---

### 3. Tạo mới một Repository

- **Endpoint:** `/user/repos`
- **Method:** `POST`
- **Status Code:**
  - `201 Created`: Tạo repository thành công.
  - `401 Unauthorized`: Lỗi xác thực (chưa cung cấp token hoặc token không hợp lệ).
  - `422 Unprocessable Entity`: Lỗi dữ liệu gửi lên (ví dụ: thiếu tên repo hoặc tên đã tồn tại).
- **Headers quan trọng:**
  - _Request:_ `Authorization: Bearer <YOUR-TOKEN>`, `Content-Type: application/json`
- **Có RESTful không?**: **Có.** Endpoint trỏ đến tập hợp `repos` của user hiện tại. Hành động tạo mới tài nguyên được thực hiện thông qua method `POST`. Trả về mã lỗi `201 Created` thay vì 200 cũng là một Best Practice của REST.

---

### 4. Cập nhật thông tin Repository

- **Endpoint:** `/repos/{owner}/{repo}`
- **Method:** `PATCH`
- **Status Code:**
  - `200 OK`: Cập nhật thành công và trả về thông tin repo mới.
  - `403 Forbidden`: Người dùng không có quyền chỉnh sửa repo này.
  - `404 Not Found`: Không tìm thấy repo.
- **Headers quan trọng:**
  - _Request:_ `Authorization: Bearer <YOUR-TOKEN>`, `Content-Type: application/json`
- **Có RESTful không?**: **Có.** RESTful khuyến nghị dùng `PUT` để thay thế toàn bộ tài nguyên và `PATCH` để cập nhật một phần tài nguyên. Ở đây GitHub dùng `PATCH` vì người dùng thường chỉ gửi lên một vài trường cần đổi (như `description`) chứ không gửi lại toàn bộ object.

---

### 5. Xóa một Repository

- **Endpoint:** `/repos/{owner}/{repo}`
- **Method:** `DELETE`
- **Status Code:**
  - `204 No Content`: Xóa thành công (không có dữ liệu trả về trong body).
  - `403 Forbidden`: Người dùng không đủ quyền admin để xóa.
  - `404 Not Found`: Repository không tồn tại.
- **Headers quan trọng:**
  - _Request:_ `Authorization: Bearer <YOUR-TOKEN>`
- **Có RESTful không?**: **Có.** Method `DELETE` được ánh xạ chính xác với hành động xóa tài nguyên. Việc server trả về status `204 No Content` là chuẩn xác theo chuẩn HTTP/REST vì sau khi xóa, không có dữ liệu tài nguyên nào cần trả về cho client.

---
