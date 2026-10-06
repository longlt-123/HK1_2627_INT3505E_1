## 1. GET `orders` theo `status`
Lệnh powershell: `curl.exe -i "http://127.0.0.1:5000/api/v1/orders?status=paid"`

Kết quả:

![GET orders theo status](./images/lab3_1.png)

## 2. GET `orders` với `limit=5`
Lệnh powershell: `curl.exe -i "http://127.0.0.1:5000/api/v1/orders?limit=5"`

Kết quả:

![GET orders với limit](./images/lab3_3.png)

## 3. GET `orders` với sparse fieldsets
Lệnh powershell: `curl.exe -i "http://127.0.0.1:5000/api/v1/orders?fields=id,total"`

Kết quả:

![GET orders với sparse fieldsets](./images/lab3_7.png)

## 4. GET `orders` theo `customer_id`
Lệnh powershell: `curl.exe -i "http://127.0.0.1:5000/api/v1/orders?customer_id=101"`

Kết quả:

![GET orders theo customer_id](./images/lab3_2.png)

## 5. GET `orders` với `sort`
Lệnh powershell: `curl.exe -i "http://127.0.0.1:5000/api/v1/orders?sort=-total"`

Kết quả:

![GET orders với sort giảm dần theo total](./images/lab3_6.png)

## 6. Cursor pagination - lấy trang tiếp theo
Trước tiên lấy trang đầu với `limit=5`:

Lệnh powershell: `$r = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/v1/orders?limit=5"`

Lấy `next_cursor`:

Lệnh powershell: `$cursor = $r.pagination.next_cursor`

Dùng cursor để lấy trang tiếp theo:

Lệnh powershell: `Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/v1/orders?limit=5&cursor=$cursor"`

Kết quả:

![Cursor pagination lấy trang tiếp theo](./images/lab3_4.png)

## 7. Cursor không hợp lệ - 400 Bad Request
Lệnh powershell: `curl.exe -i "http://127.0.0.1:5000/api/v1/orders?cursor=abcxyz"`

Kết quả:

![Cursor không hợp lệ trả về 400](./images/lab3_5.png)

## 8. Kết hợp filter, sort, sparse fieldsets và limit
Lệnh powershell: `curl.exe -i "http://127.0.0.1:5000/api/v1/orders?status=paid&customer_id=101&sort=-total&fields=id,total&limit=2"`

Kết quả:

![Kết hợp filter sort fields và limit](./images/lab3_8.png)
