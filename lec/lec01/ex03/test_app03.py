import unittest
import json

from app03 import app, STUDENTS 

class TestStudentAPI(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        
        STUDENTS.clear() 

    def test_create_student_success(self):
        """ Kiểm tra trường hợp tạo sinh viên thành công khi gửi đầy đủ thông tin """
        payload = {
            "name": "Nguyễn Văn A",
            "gpa": 3.8
        }
        
        response = self.client.post(
            '/students',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        data = response.get_json()
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data["name"], "Nguyễn Văn A")
        self.assertEqual(data["gpa"], 3.8)
        self.assertIn("id", data)
        
        self.assertEqual(len(STUDENTS), 1)

    def test_create_student_missing_name(self):
        """ Kiểm tra trường hợp API báo lỗi 400 khi request bị thiếu trường 'name' """
        payload = {
            "gpa": 3.5
        }
        
        response = self.client.post(
            '/students',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        data = response.get_json()
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data["error"], "name là bắt buộc")
        
        self.assertEqual(len(STUDENTS), 0)

    def test_create_student_default_gpa(self):
        """ Kiểm tra API có tự động gán giá trị GPA mặc định khi chỉ gửi tên sinh viên hay không """
        payload = {
            "name": "Trần Thị B"
        }
        
        response = self.client.post(
            '/students',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        data = response.get_json()
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data["name"], "Trần Thị B")
        self.assertEqual(data["gpa"], 0.0)

if __name__ == '__main__':
    unittest.main()