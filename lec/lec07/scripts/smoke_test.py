"""Exercise a running API over HTTP, including concurrent stock reservations.

Usage: python lec/lec07/scripts/smoke_test.py [http://127.0.0.1:5000]
Creates products with unique SMOKE-* SKUs and one order in the target database.
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


def main():
    base = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000").rstrip("/")

    def request(method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = Request(base + path, data=data, method=method,
                      headers={"Content-Type": "application/json"})
        try:
            response = urlopen(req, timeout=15)
        except HTTPError as error:
            response = error
        with response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None

    for path in ("/healthz", "/ready"):
        assert request("GET", path)[0] == 200
    prefix = uuid4().hex[:8]
    products = []
    for i, stock in enumerate((5, 3, 1)):
        status, product = request("POST", "/api/v1/products", {
            "sku": f"SMOKE-{prefix}-{i}", "name": "Smoke test",
            "price_cents": 1250, "qty_in_stock": stock,
        })
        assert status == 201, product
        products.append(product)
    first, second, concurrent = products
    status, order = request("POST", "/api/v1/orders", {"items": [
        {"product_id": first["id"], "qty": 2},
        {"product_id": second["id"], "qty": 3},
    ]})
    assert status == 201, order
    assert order["total_cents"] == 6250
    assert request("GET", f"/api/v1/orders/{order['id']}")[1]["total_cents"] == 6250
    assert request("GET", "/api/v1/orders")[0] == 200
    status, error = request("POST", "/api/v1/orders", {"items": [
        {"product_id": first["id"], "qty": 1},
        {"product_id": second["id"], "qty": 1},
    ]})
    assert status == 409, error
    assert request("GET", f"/api/v1/products/{first['id']}")[1]["qty_in_stock"] == 3

    def reserve(_):
        return request("POST", f"/api/v1/products/{concurrent['id']}/reserve", {"qty": 1})[0]

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = sorted(executor.map(reserve, range(2)))
    assert statuses == [200, 409], statuses
    assert request("GET", f"/api/v1/products/{concurrent['id']}")[1]["qty_in_stock"] == 0
    assert request("DELETE", f"/api/v1/products/{first['id']}")[0] == 204
    assert request("GET", f"/api/v1/products/{first['id']}")[0] == 404
    print("PASS: health, products, orders, rollback, concurrent reserve, soft delete")


if __name__ == "__main__":
    main()
