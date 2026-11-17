# Lab01 — pytest

Kết quả test:
![Chạy test](/lec/lec08/lab08-starter/images/image.png)

# Lab03 — Postman/Newman

Đã hoàn thành 5 happy-path requests và folder `error-cases` gồm POST thiếu `title` (400) và GET `/books/9999` (404). Mỗi request có 2 `pm.test`: status và body. POST lưu `book_id` bằng `pm.collectionVariables`, GET/PUT/DELETE dùng lại ID này.

| Folder | Request | Status | Kiểm tra body |
|---|---|---|---|
| books | GET `/books` | 200 | JSON array |
| books | POST `/books` | 201 | Đúng dữ liệu tạo, `id` nguyên dương |
| books | GET `/books/{{book_id}}` | 200 | Đúng sách vừa tạo |
| books | PUT `/books/{{book_id}}` | 200 | Đúng ID và nội dung cập nhật |
| books | DELETE `/books/{{book_id}}` | 204 | Body rỗng |
| error-cases | POST `/books` thiếu `title` | 400 | `VALIDATION_ERROR`, `Invalid book data`, chi tiết thiếu `title` |
| error-cases | GET `/books/9999` | 404 | `NOT_FOUND`, `Book not found` |

POST xóa `book_id` cũ trước khi chạy và lưu ID mới bằng `pm.collectionVariables.set("book_id", book.id)` khi response hợp lệ

Kết quả chạy thực tế ngày 17/11/2026:
![Chạy test](/lec/lec08/lab08-starter/images/postman-newman.png)

- 7 requests, 14 assertions, 0 failures.
- [JUnit report](reports/junit.xml) có **14 phần tử `testcase`**, không có failure/error.

```powershell
newman.cmd run books-api.postman_collection.json -e postman/local.postman_environment.json -r cli,junit --reporter-junit-export reports/junit.xml
```
