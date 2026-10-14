import unittest
import openapi_server
from flask import json

from openapi_server.models.modify_petwith_id_request import ModifyPetwithIDRequest  # noqa: E501
from openapi_server.models.pet import Pet  # noqa: E501
from openapi_server.models.pets_post400_response import PetsPost400Response  # noqa: E501
from openapi_server.test import BaseTestCase


class TestPetController(BaseTestCase):
    """PetController integration test stubs"""

    def test_delete_petwith_id(self):
        """Test case for delete_petwith_id

        Xóa thú cưng theo ID
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/vnu-12e/PetStore/1.0.0/pets/{pet_id}'.format(pet_id=56),
            method='DELETE',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_pets(self):
        """Test case for get_pets

        Lấy danh sách toàn bộ thú cưng
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/vnu-12e/PetStore/1.0.0/pets',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_petwith_id(self):
        """Test case for get_petwith_id

        Lấy thông tin chi tiết một thú cưng theo ID
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/vnu-12e/PetStore/1.0.0/pets/{pet_id}'.format(pet_id=56),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_modify_petwith_id(self):
        """Test case for modify_petwith_id

        Sửa đổi thông tin của thú cưng
        """
        modify_petwith_id_request = openapi_server.ModifyPetwithIDRequest()
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/vnu-12e/PetStore/1.0.0/pets/{pet_id}'.format(pet_id=56),
            method='PATCH',
            headers=headers,
            data=json.dumps(modify_petwith_id_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_pets_pet_id_put(self):
        """Test case for pets_pet_id_put

        Cập nhật thông tin thú cưng
        """
        pet = {"id":10,"name":"Doggie","category":"Chó","status":"available"}
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/vnu-12e/PetStore/1.0.0/pets/{pet_id}'.format(pet_id=56),
            method='PUT',
            headers=headers,
            data=json.dumps(pet),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_pets_post(self):
        """Test case for pets_post

        Thêm thú cưng mới
        """
        pet = {"id":10,"name":"Doggie","category":"Chó","status":"available"}
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/vnu-12e/PetStore/1.0.0/pets',
            method='POST',
            headers=headers,
            data=json.dumps(pet),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
