import unittest
import json
from app03 import app

class Exercise3Test(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_create_valid_student_name_and_with_gpa(self):
        payload = {"id": 21, "name": "An", "gpa":3.4}
        response = self.client.post(
            "/students",
            data = json.dumps(payload),
            content_type='application/json'
        )

        data = response.get_json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(data, payload)

    def test_create_valid_student_name_and_without_gpa(self):
        payload = {"id": 21, "name": "An"}
        response = self.client.post(
            "/students",
            data = json.dumps(payload),
            content_type='application/json'
        )

        data = response.get_json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual({"id": data.get("id"), "name": data.get("name")}, payload)
        self.assertEqual(data.get("gpa"), 0.0)

    def test_create_invalid_student_name(self):
            payload = {"id": 21, "gpa":3.4}
            response = self.client.post(
                "/students",
                data = json.dumps(payload),
                content_type='application/json'
            )
    
            data = response.get_json()
    
            self.assertEqual(response.status_code, 400)
            self.assertEqual(data, {"error": "name là bắt buộc"})

if __name__ == '__main__':
    unittest.main()
