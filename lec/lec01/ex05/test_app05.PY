import unittest
from app05 import app, ORDERS

class TestOrderAPI(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        
        ORDERS.clear()
        ORDERS.update({
            "1": {"id": "1", "status": "pending"},
            "2": {"id": "2", "status": "shipped"},
            "3": {"id": "3", "status": "delivered"}
        })

    def test_delete_order_success(self):
        """ Kiểm tra xóa đơn hàng thành công và trả về mã 204 No Content """
        response = self.client.delete('/orders/1')
        
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b"")
        self.assertNotIn("1", ORDERS)

    def test_delete_order_not_found(self):
        """ Kiểm tra trường hợp trả về lỗi 404 khi cố gắng xóa một đơn hàng không tồn tại """
        response = self.client.delete('/orders/999')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data["error"], "not found")

    def test_delete_order_shipped(self):
        """ Kiểm tra luật nghiệp vụ: Không cho phép xóa đơn hàng đã "shipped" mã 409 """
        response = self.client.delete('/orders/2')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 409)
        self.assertEqual(data["error"], "cannot delete")
        self.assertIn("2", ORDERS)

    def test_delete_order_delivered(self):
        """ Kiểm tra luật nghiệp vụ: Không cho phép xóa đơn hàng đã "delivered" mã 409 """
        response = self.client.delete('/orders/3')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 409)
        self.assertEqual(data["error"], "cannot delete")
        self.assertIn("3", ORDERS)

if __name__ == '__main__':
    unittest.main()