from flask import Flask
from .extensions import db, migrate
import os


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///products.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)

    from .api.products import products_bp
    app.register_blueprint(products_bp)

    @app.cli.command("init-db")
    def init_db():
        db.create_all()

    return app
