import unittest
import json
from app02 import app 

class Exercise2Test(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_health_endpoint(self):
        """ Kiểm tra endpoint/health có hoạt động bình thường không """
        response = self.client.get('/health')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {"status": "ok"})

    def test_echo_endpoint_with_valid_json(self):
        """ Kiểm tra endpoint/echo có phản hồi chính xác cục dữ liệu JSON đã gửi lên không """
        payload = {"name": "An", "age": 21}
        response = self.client.post(
            '/echo',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {"you_sent": payload})

    def test_echo_endpoint_with_invalid_json(self):
        """ Kiểm tra khả năng xử lý an toàn của API khi nhận được dữ liệu không phải định dạng JSON """
        response = self.client.post(
            '/echo',
            data="Lỗi cố ý không phải JSON",
            content_type='application/json'
        )
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {"you_sent": {}})

if __name__ == '__main__':
    unittest.main()