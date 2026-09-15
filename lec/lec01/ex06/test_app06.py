import unittest
import json
import app06
from app06 import app, BOOKS

class TestBooksAPI(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        
        BOOKS.clear()
        BOOKS.extend([
            {"id": 1, "title": "Clean Code", "author": "R. Martin"},
            {"id": 2, "title": "Pragmatic Programmer", "author": "Andy Hunt"}
        ])
        app06._next = 3

    def test_get_list(self):
        """ Test lấy danh sách tất cả sách """
        response = self.client.get('/books')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[1]["id"], 2)

    def test_get_detail_not_found(self):
        """ Test lấy chi tiết một cuốn sách với ID không tồn tại """
        response = self.client.get('/books/999')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data["error"], "not found")

    def test_post_create_success(self):
        """ Test tạo mới sách thành công """
        payload = {"title": "DDIA", "author": "Kleppmann"}
        
        response = self.client.post(
            '/books',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = response.get_json()
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data["id"], 3)
        self.assertEqual(data["title"], "DDIA")
        self.assertEqual(data["author"], "Kleppmann")
        
        self.assertIn("Location", response.headers)
        self.assertEqual(response.headers["Location"], "/books/3")
        self.assertEqual(len(BOOKS), 3)

    def test_put_update_success(self):
        """ Test cập nhật title sách """
        payload = {"title": "CC 2nd ed."}
        
        response = self.client.put(
            '/books/1',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["title"], "CC 2nd ed.") 
        self.assertEqual(data["author"], "R. Martin")

    def test_delete_success(self):
        """ Test xóa sách thành công """
        response = self.client.delete('/books/2')
        
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b"")
        
        self.assertEqual(len(BOOKS), 1)

    def test_post_create_bad_request(self):
        """ Test tạo sách nhưng gửi payload rỗng {} """
        payload = {}
        
        response = self.client.post(
            '/books',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = response.get_json()
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data["error"], "need title + author") 

if __name__ == '__main__':
    unittest.main()