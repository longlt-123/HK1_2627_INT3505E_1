import unittest
import app

class TestRESTfulBooksAPI(unittest.TestCase):
    def setUp(self):
        app.app.config["TESTING"] = True
        self.client = app.app.test_client()
                
        app.BOOKS.clear()
        app.BOOKS.extend([
            {"id": 1, "title": "Clean Code", "author": "R. Martin", "year": 2008, "price": 34.49},
            {"id": 2, "title": "Pragmatic Programmer", "author": "Andy Hunt", "year": 1999, "price": 39.99}
        ])
        app._next_id = 3

    # ----------------------- GET TEST ----------------------- #
    def test_get_list_books(self):
        """ Test lấy danh sách tất cả sách """
        response = self.client.get('/books')
        
        json_resp = response.get_json()
        data = json_resp["data"] 
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[1]["id"], 2)

    def test_filter_by_q(self):
        """ Test search theo Title (không phân biệt hoa thường) """
        response = self.client.get("/books?q=CLEAN")
        data = response.get_json()
        
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["title"], "Clean Code")
        self.assertEqual(data["pagination"]["total"], 1)

    def test_filter_by_author(self):
        """ Test search theo Author chính xác """
        response = self.client.get("/books?author=andy hunt")
        data = response.get_json()
        
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["author"], "Andy Hunt")

    def test_limit(self):
        """ Test tham số limit có tác động chuẩn vào total hay không """
        response = self.client.get("/books?limit=1")
        data = response.get_json()
        
        self.assertEqual(data["pagination"]["total"], 1)
        self.assertEqual(len(data["data"]), 1)

    def test_sort_string(self):
        """ Test sắp xếp theo key chữ (title) """
        response = self.client.get("/books?sort=title")
        data = response.get_json()
        self.assertEqual(data["data"][0]["title"], "Clean Code")

    def test_sort_integer(self):
        """ Test sắp xếp theo key số (year) """
        response = self.client.get("/books?sort=year")
        data = response.get_json()
        self.assertEqual(data["data"][0]["year"], 1999)

    def test_sort_invalid_key_safe_hateoas(self):
        """ Test đảm bảo server không sập (trả về 200) khi truyền key sort ảo """
        response = self.client.get("/books?sort=not_exist_key")
        self.assertEqual(response.status_code, 200)

    def test_get_exist_book(self):
        """ Test lấy chi tiết của một cuốn sách theo ID """
        response = self.client.get('/books/1')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, app.BOOKS[0])

    def test_not_found_book(self):
        """ Test lấy chi tiết một cuốn sách với ID không tồn tại """
        response = self.client.get('/books/9999')
        data = response.get_json()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data, {"error": "not found"})

    # ----------------------- POST TEST ----------------------- #
    def test_create_book_success(self):
        """ Test tạo một cuốn sách mới thành công """
        new_book = {"title": "Design Patterns", "author": "Gang of Four", "year": 1994, "price": 45.0}
        response = self.client.post('/books', json=new_book)
        data = response.get_json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(data["title"], "Design Patterns")
        self.assertEqual(data["id"], 3)
        self.assertEqual(len(app.BOOKS), 3)
        self.assertEqual(response.headers.get("Location"), "/books/3")

    def test_create_book_missing_fields(self):
        """ Test tạo sách nhưng thiếu title hoặc author """
        bad_book = {"year": 2020}
        response = self.client.post('/books', json=bad_book)
        data = response.get_json()

        self.assertEqual(response.status_code, 422)
        self.assertEqual(data["error"], "title and author required")

    def test_create_book_invalid_year(self):
        """ Test tạo sách với năm xuất bản không hợp lệ (< 1900) """
        bad_book = {"title": "History", "author": "Unknown", "year": 1800}
        response = self.client.post('/books', json=bad_book)
        data = response.get_json()
        
        self.assertEqual(response.status_code, 409)
        self.assertEqual(data["error"], "year must be a valid number >= 1900")

    def test_create_book_invalid_price(self):
            """ Test tạo sách với giá không hợp lệ (< 0) """
            bad_book = {"title": "History", "author": "Unknown", "price": -3.2}
            response = self.client.post('/books', json=bad_book)
            data = response.get_json()
            
            self.assertEqual(response.status_code, 409)
            self.assertEqual(data["error"], "price must be a valid number >= 0")

    # ----------------------- PUT TEST ----------------------- #
    def test_put_book_success(self):
        """ Test cập nhật toàn bộ thông tin sách thành công """
        updated_data = {"title": "Clean Code - Revised", "author": "Robert C. Martin", "year": 2012, "price": 40.0}
        response = self.client.put('/books/1', json=updated_data)
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["title"], "Clean Code - Revised")
        self.assertEqual(app.BOOKS[0]["author"], "Robert C. Martin")
        self.assertEqual(data, app.BOOKS[0])

    def test_put_book_missing_not_important_field_success(self):
        """ Test cập nhật toàn bộ thông tin sách (thiếu year và price) thành công """
        updated_data = {"title": "Clean Code - Revised", "author": "Robert C. Martin"}
        response = self.client.put('/books/1', json=updated_data)
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["title"], "Clean Code - Revised")
        self.assertEqual(app.BOOKS[0]["author"], "Robert C. Martin")
        self.assertEqual(app.BOOKS[0]["year"], "unk")
        self.assertEqual(app.BOOKS[0]["price"], "unk")

    def test_put_book_not_found(self):
        """ Test cập nhật toàn bộ một cuốn sách không tồn tại """
        updated_data = {"title": "Some Book", "author": "Some Author"}
        response = self.client.put('/books/999', json=updated_data)
        data = response.get_json()
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data, {"error": "not found"})

    def test_put_book_missing_fields(self):
        """ Test cập nhật toàn bộ nhưng thiếu trường bắt buộc """
        bad_data = {"title": "Just Title"}
        response = self.client.put('/books/1', json=bad_data)
        data = response.get_json()
        
        self.assertEqual(response.status_code, 422)
        self.assertEqual(data["error"], "title and author require")

    # ----------------------- PATCH TEST ----------------------- #
    def test_patch_book_success(self):
        """ Test cập nhật một phần thông tin sách thành công """
        patch_data = {"price": 25.00}
        response = self.client.patch('/books/2', json=patch_data)
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["price"], 25.00)
        self.assertEqual(data["title"], "Pragmatic Programmer")
        self.assertEqual(app.BOOKS[1]["price"], 25.00)

    def test_patch_book_not_found(self):
        """ Test cập nhật một phần cuốn sách không tồn tại """
        patch_data = {"price": 10.0}
        response = self.client.patch('/books/999', json=patch_data)
        data = response.get_json()
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data["error"], "not found")

    def test_patch_book_invalid_price(self):
        """ Test cập nhật một phần với giá trị sai (price < 0) """
        patch_data = {"price": -5.0}
        response = self.client.patch('/books/2', json=patch_data)
        
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.get_json()["error"], "price must be positive")

    # ----------------------- DELETE TEST ----------------------- #
    def test_delete_book_success(self):
        """ Test xóa một cuốn sách thành công """
        initial_length = len(app.BOOKS)
        response = self.client.delete('/books/1')
        
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(app.BOOKS), initial_length - 1)
        self.assertIsNone(app.find(1))

    def test_delete_book_not_found(self):
        """ Test xóa một cuốn sách không tồn tại """
        response = self.client.delete('/books/999')
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"], "not found")

    # ----------------------- HATEOAS & PAGINATION TEST ----------------------- #
    def test_empty_books_hateoas(self):
        """ Test cấu trúc trả về khi database không có sách """
        app.BOOKS.clear()
        response = self.client.get("/books")
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["data"], [])
        self.assertIsNone(data.get("pagination"))
        self.assertEqual(data.get("_links"), {})

    def test_invalid_parameters_hateoas(self):
        """ Test lỗi 400 khi truyền string vào page hoặc size """
        response = self.client.get("/books?page=abc")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_default_pagination_hateoas(self):
        """ Test lấy danh sách mặc định (không filter, mặc định size lớn hơn tổng số sách) """
        response = self.client.get("/books")
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data["data"]), 2) 
        self.assertEqual(data["pagination"]["total"], 2)
        self.assertEqual(data["pagination"]["page"], 1)
        
        links = data["_links"]
        self.assertIn("self", links)
        self.assertIn("first", links)
        self.assertIn("last", links)
        self.assertNotIn("prev", links)
        self.assertNotIn("next", links)

    def test_pagination_logic_hateoas(self):
        """ Test cắt trang (page, size) và tự động sinh prev/next link """
        response1 = self.client.get("/books?page=1&size=1")
        data1 = response1.get_json()
        
        self.assertEqual(len(data1["data"]), 1)
        self.assertEqual(data1["data"][0]["title"], "Clean Code")
        
        links1 = data1["_links"]
        self.assertIn("next", links1)
        self.assertNotIn("prev", links1)
        self.assertIn("page=2", links1["next"]["href"])

        response2 = self.client.get("/books?page=2&size=1")
        data2 = response2.get_json()
        
        self.assertEqual(len(data2["data"]), 1)
        self.assertEqual(data2["data"][0]["title"], "Pragmatic Programmer")
        
        links2 = data2["_links"]
        self.assertIn("prev", links2)
        self.assertNotIn("next", links2)
        self.assertIn("page=1", links2["prev"]["href"])

if __name__ == "__main__":
    unittest.main()