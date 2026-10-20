import pytest
from app import create_app
from models import db
from seed import seed_data


@pytest.fixture()
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://",
                      "SECRET_KEY": "test-key"})
    with app.app_context():
        db.create_all()
        seed_data()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
