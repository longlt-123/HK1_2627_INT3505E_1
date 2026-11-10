import pytest

from lec.lec07.extensions import db
from lec.lec07.models import Order, OrderItem

URL = "/api/v1/orders"


def test_post_order_multiple_products(client, make_product):
    first = make_product(qty_in_stock=5)
    second = make_product(sku="BOOK-001", price_cents=2000, qty_in_stock=3)
    response = client.post(URL, json={"items": [
        {"product_id": first["id"], "qty": 2},
        {"product_id": second["id"], "qty": 3},
    ]})
    assert response.status_code == 201
    assert response.headers["Location"] == f"{URL}/{response.json['id']}"
    assert response.json["total_cents"] == 8500
    assert len(response.json["items"]) == 2
    assert client.get(f"/api/v1/products/{first['id']}").json["qty_in_stock"] == 3
    assert client.get(f"/api/v1/products/{second['id']}").json["qty_in_stock"] == 0


@pytest.mark.parametrize("failure", ["insufficient", "missing", "archived"])
def test_failed_order_rolls_back_every_item(app, client, make_product, failure):
    first = make_product(qty_in_stock=5)
    second = make_product(sku="BOOK-001", qty_in_stock=0)
    second_id = second["id"]
    status = 409
    if failure == "missing":
        second_id = 999
        status = 404
    elif failure == "archived":
        client.delete(f"/api/v1/products/{second_id}")
        status = 404
    response = client.post(URL, json={"items": [
        {"product_id": first["id"], "qty": 2},
        {"product_id": second_id, "qty": 1},
    ]})
    assert response.status_code == status
    assert set(response.json) == {"error", "detail"}
    assert client.get(f"/api/v1/products/{first['id']}").json["qty_in_stock"] == 5
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(Order)) == 0
        assert db.session.scalar(db.select(db.func.count()).select_from(OrderItem)) == 0


@pytest.mark.parametrize("body", [
    {}, {"items": []}, {"items": [{}]}, {"items": [{"product_id": 1, "qty": 0}]},
    {"items": [{"product_id": 1, "qty": 1.2}]},
    {"items": [{"product_id": True, "qty": 1}]},
    {"items": [{"product_id": 1, "qty": 1}, {"product_id": 1, "qty": 2}]},
    {"items": [{"product_id": 1, "qty": 1, "unit_price_cents": 0}]},
])
def test_post_order_validation(client, body):
    response = client.post(URL, json=body)
    assert response.status_code == 422
    assert response.json["error"] == "validation_error"


@pytest.mark.parametrize("number_of_orders", [1, 10])
def test_get_orders_eager_loading(client, make_product, select_queries, number_of_orders):
    for i in range(number_of_orders):
        # Distinct products ensure the identity map cannot hide an N+1 bug.
        product = make_product(sku=f"SKU-{i}")
        assert client.post(URL, json={"items": [
            {"product_id": product["id"], "qty": 1},
        ]}).status_code == 201
    select_queries.clear()
    response = client.get(URL)
    assert response.status_code == 200
    assert response.json["total"] == number_of_orders
    assert len(response.json["items"]) == number_of_orders
    assert all(order["items"][0]["product"]["sku"] for order in response.json["items"])
    # Orders + items + products + COUNT; stays constant as the dataset grows.
    assert len(select_queries) == 4, select_queries


def test_get_order_eager_loading_and_price_snapshot(client, make_product, select_queries):
    product = make_product()
    order = client.post(URL, json={"items": [{"product_id": product["id"], "qty": 2}]}).json
    client.patch(f"/api/v1/products/{product['id']}", json={"price_cents": 9999})
    client.delete(f"/api/v1/products/{product['id']}")
    select_queries.clear()
    response = client.get(f"{URL}/{order['id']}")
    assert response.status_code == 200
    assert response.json["total_cents"] == 2500
    assert response.json["items"][0]["unit_price_cents"] == 1250
    assert response.json["items"][0]["product"]["archived"] is True
    assert len(select_queries) == 3, select_queries


def test_order_pagination_and_missing(client, make_product):
    product = make_product()
    for _ in range(3):
        assert client.post(URL, json={"items": [{"product_id": product["id"], "qty": 1}]}).status_code == 201
    page = client.get(URL + "?page=2&size=2").json
    assert page["total"] == 3
    assert len(page["items"]) == 1
    assert page["page"] == 2
    assert client.get(URL + "/999").status_code == 404
