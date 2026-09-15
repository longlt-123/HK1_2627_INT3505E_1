import unittest
import json
from app01 import app 

class Exercise1Test(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_first_endpoint(self):
        """ Kiểm tra endpoint/ có hoạt động đúng và trả về "Hello, API!" không """
        response = self.client.get('/')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {"message": "Hello, API!"})

if __name__ == '__main__':
    unittest.main()