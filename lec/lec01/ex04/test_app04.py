import unittest
from app04 import app

class TestAppAPI(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_get_book_by_id_success(self):
        """Test lấy thông tin sách thành công (id tồn tại)"""
        response = self.client.get('/books/1')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["name"], "Harry Potter")
        self.assertEqual(data["id"], "1")

    def test_get_book_by_id_not_found(self):
        """Test lấy sách thất bại (id không tồn tại)"""
        response = self.client.get('/books/999')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data["error"], "not found")

    def test_get_item_success(self):
        """Test API nhận tham số kiểu int trên URL"""
        response = self.client.get('/items/42')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["id"], 42) 
        self.assertIsInstance(data["id"], int) # Đảm bảo trả về đúng kiểu int

    def test_get_item_wrong_type(self):
        """Test API khi truyền tham số sai kiểu (string thay vì int)"""
        response = self.client.get('/items/abc')
        self.assertEqual(response.status_code, 404)

    def test_list_books_no_query(self):
        """Test lấy danh sách sách không truyền query params"""
        response = self.client.get('/books')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2) # Có 2 cuốn sách trong list mặc định

    def test_list_books_with_query_q(self):
        """Test lấy danh sách sách có truyền tham số tìm kiếm ?q="""
        response = self.client.get('/books?q=lord')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["name"], "Lord of the Rings")

    def test_list_books_with_limit(self):
        """Test lấy danh sách sách có giới hạn ?limit="""
        response = self.client.get('/books?limit=1')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data["items"]), 1)

if __name__ == '__main__':
    unittest.main()