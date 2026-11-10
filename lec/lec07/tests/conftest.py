import pytest
from sqlalchemy import event

from lec.lec07.extensions import db
from lec.lec07.factory import create_app


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "LOG_LEVEL": "WARNING",
    })
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_product(client):
    def create(**overrides):
        body = {"sku": "PEN-001", "name": "Pen", "price_cents": 1250, "qty_in_stock": 20}
        body.update(overrides)
        response = client.post("/api/v1/products", json=body)
        assert response.status_code == 201, response.json
        return response.json
    return create


@pytest.fixture
def select_queries(app):
    queries = []

    def capture(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            queries.append(statement)

    with app.app_context():
        engine = db.engine
    event.listen(engine, "before_cursor_execute", capture)
    yield queries
    event.remove(engine, "before_cursor_execute", capture)
