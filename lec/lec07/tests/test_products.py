import unittest

from lec.lec07.extensions import db
from lec.lec07.factory import create_app


class ProductsTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()
        self.url = "/api/v1/products"
        response = self.client.post(self.url, json={
            "sku": "ABC", "name": "Pen", "price_cents": 1250, "qty_in_stock": 5,
        })
        self.assertEqual(response.status_code, 201)
        self.product_url = f"{self.url}/{response.json['id']}"

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_get_and_missing_product(self):
        response = self.client.get(self.product_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["price_cents"], 1250)
        self.assertEqual(self.client.get(f"{self.url}/999").status_code, 404)

    def test_reserve_and_insufficient_stock(self):
        response = self.client.post(self.product_url + "/reserve", json={"qty": 3})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["qty_in_stock"], 2)
        response = self.client.post(self.product_url + "/reserve", json={"qty": 3})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.client.get(self.product_url).json["qty_in_stock"], 2)
        response = self.client.post(self.product_url + "/reserve", json={"qty": 2})
        self.assertEqual(response.json["qty_in_stock"], 0)

    def test_invalid_quantity(self):
        for body in ({}, {"qty": 0}, {"qty": -1}, {"qty": 1.5}, {"qty": True}, {"qty": "2"}):
            with self.subTest(body=body):
                response = self.client.post(self.product_url + "/reserve", json=body)
                self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.get(self.product_url).json["qty_in_stock"], 5)

    def test_missing_and_archived_reservations(self):
        self.assertEqual(self.client.post(f"{self.url}/999/reserve", json={"qty": 1}).status_code, 404)
        self.assertEqual(self.client.delete(self.product_url).status_code, 204)
        self.assertEqual(self.client.get(self.product_url).status_code, 404)
        self.assertEqual(self.client.post(self.product_url + "/reserve", json={"qty": 1}).status_code, 404)
        self.assertEqual(self.client.get(self.url).json["total"], 0)

    def test_create_validation_and_duplicate(self):
        self.assertEqual(self.client.post(self.url, json={"sku": "XYZ", "name": "Pen"}).status_code, 422)
        response = self.client.post(self.url, json={"sku": "ABC", "name": "Pen", "price_cents": 100})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.client.get(self.url + "?page=abc").status_code, 400)
