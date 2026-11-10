import pytest

URL = "/api/v1/products"


@pytest.mark.parametrize("changes", [
    {"sku": "ab"}, {"sku": "x" * 33}, {"name": ""}, {"name": "   "},
    {"name": "x" * 256}, {"price_cents": -1}, {"price_cents": 1.5},
    {"price_cents": True}, {"qty_in_stock": -1}, {"qty_in_stock": 1.5},
    {"archived": True},
])
def test_product_input_contract(client, changes):
    body = {"sku": "ABC", "name": "Pen", "price_cents": 100}
    body.update(changes)
    response = client.post(URL, json=body)
    assert response.status_code == 422
    assert set(response.json) == {"error", "detail"}
    assert client.get(URL).json["total"] == 0


def test_default_stock_and_partial_update(client):
    product = client.post(URL, json={"sku": "ABC", "name": "Pen", "price_cents": 0}).json
    assert product["qty_in_stock"] == 0
    path = f"{URL}/{product['id']}"
    response = client.patch(path, json={"name": "New name", "description": "Blue"})
    assert response.status_code == 200
    assert response.json["name"] == "New name"
    assert response.json["sku"] == "ABC"
    assert response.json["price_cents"] == 0
    assert client.patch(path, json={"description": None}).json["description"] is None
    assert client.patch(path, json={"price_cents": -1}).status_code == 422
    assert client.patch(path, json={"qty_in_stock": 10}).status_code == 422
    assert client.get(path).json["qty_in_stock"] == 0


def test_pagination_and_soft_delete(client, make_product):
    products = [make_product(sku=f"SKU-{i}") for i in range(4)]
    assert client.delete(f"{URL}/{products[0]['id']}").status_code == 204
    response = client.get(URL + "?page=2&size=2")
    assert response.json["total"] == 3
    assert response.json["page"] == 2
    assert response.json["size"] == 2
    assert [p["id"] for p in response.json["items"]] == [products[3]["id"]]
    assert client.get(URL + "?page=0&size=999").json["size"] == 100
    assert client.get(URL + "?page=10").json["items"] == []
    assert client.patch(f"{URL}/{products[0]['id']}", json={"name": "Changed"}).status_code == 404


def test_json_and_http_errors(client):
    for kwargs in (
        {"data": "{bad", "content_type": "application/json"},
        {"data": "{}", "content_type": "text/plain"},
    ):
        response = client.post(URL, **kwargs)
        assert response.status_code == 400
        assert set(response.json) == {"error", "detail"}
    response = client.get(URL + "/999")
    assert response.status_code == 404
    assert set(response.json) == {"error", "detail"}
    response = client.put(URL)
    assert response.status_code == 405
    assert "GET" in response.headers["Allow"]
