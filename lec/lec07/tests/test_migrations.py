from flask_migrate import downgrade, upgrade
from sqlalchemy import inspect

from lec.lec07.extensions import db
from lec.lec07.factory import create_app


def test_migration_upgrade_downgrade_and_api():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://", "LOG_LEVEL": "WARNING"})
    with app.app_context():
        upgrade()
        assert {"products", "orders", "order_items"} <= set(inspect(db.engine).get_table_names())
        client = app.test_client()
        product = client.post("/api/v1/products", json={
            "sku": "MIG-001", "name": "Migration", "price_cents": 100, "qty_in_stock": 2,
        })
        assert product.status_code == 201
        assert client.post("/api/v1/orders", json={"items": [
            {"product_id": product.json["id"], "qty": 1},
        ]}).status_code == 201
        db.session.remove()
        downgrade(revision="base")
        assert not {"products", "orders", "order_items"} & set(inspect(db.engine).get_table_names())
        upgrade()
        assert "products" in inspect(db.engine).get_table_names()
        db.session.remove()
        db.engine.dispose()
