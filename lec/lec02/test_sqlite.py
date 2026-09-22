import unittest
import os
import sqlite

class TestSQLiteAPI(unittest.TestCase):
    def setUp(self):
        """Trỏ DB_FILE sang file test và khởi tạo dữ liệu"""
        sqlite.app.config["TESTING"] = True
        self.client = sqlite.app.test_client()
        
        sqlite.DB_FILE = 'test_database.db'
        
        if os.path.exists(sqlite.DB_FILE):
            os.remove(sqlite.DB_FILE)
            
        sqlite.init_db()

    def tearDown(self):
        """Xóa file database test đi cho sạch"""
        if os.path.exists(sqlite.DB_FILE):
            os.remove(sqlite.DB_FILE)

    # ================= TEST: GET /books (SQLite) =================
    def test_get_books_sqlite(self):
        response = self.client.get('/books')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data["data"]), 2)
        self.assertEqual(data["pagination"]["total"], 2)
        self.assertNotIn("etag", data["data"][0]) 

    def test_books_filter_and_sort_sqlite(self):
        response = self.client.get('/books?q=clean&sort=year')
        data = response.get_json()["data"]
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Clean Code")

    # ================= TEST: GET /orders =================
    def test_get_order_success(self):
        response = self.client.get('/orders/1')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["customer_name"], "John Doe")
        self.assertEqual(data["total_amount"], 74.48)

    def test_get_order_not_found(self):
        response = self.client.get('/orders/999')
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())

    # ================= TEST: ETag & If-None-Match =================
    def test_etag_conditional_request(self):
        resp1 = self.client.get('/books/1')
        self.assertEqual(resp1.status_code, 200)
        
        etag = resp1.headers.get("ETag")
        self.assertIsNotNone(etag)
        
        data1 = resp1.get_json()
        self.assertEqual(data1["title"], "Clean Code")

        headers = {"If-None-Match": etag}
        resp2 = self.client.get('/books/1', headers=headers)
        
        self.assertEqual(resp2.status_code, 304)
        self.assertEqual(resp2.data, b'') 

        headers_wrong = {"If-None-Match": "wrong_etag_123"}
        resp3 = self.client.get('/books/1', headers=headers_wrong)
        
        self.assertEqual(resp3.status_code, 200)
        self.assertEqual(resp3.get_json()["title"], "Clean Code")

if __name__ == "__main__":
    unittest.main()