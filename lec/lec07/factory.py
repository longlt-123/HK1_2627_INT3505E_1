from pathlib import Path

from flask import Flask
from sqlalchemy import event

from .config import DefaultConfig, environment_config
from .errors import register_error_handlers
from .extensions import db, migrate
from .logging_config import configure_logging


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(DefaultConfig)
    app.config.update(environment_config())
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db, directory=str(Path(__file__).parent / "migrations"))

    with app.app_context():
        if db.engine.dialect.name == "sqlite":
            @event.listens_for(db.engine, "connect")
            def enable_foreign_keys(connection, record):
                cursor = connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    from .api.health import health_bp
    from .api.orders import orders_bp
    from .api.products import products_bp
    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(health_bp)
    register_error_handlers(app)
    configure_logging(app)

    @app.cli.command("init-db")
    def init_db():
        """Create missing tables for a disposable local database; prefer db upgrade."""
        db.create_all()

    return app
