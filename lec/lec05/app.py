import os
from pathlib import Path
import click
from flask import Flask
from models import db
from errors import register_errors


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///bookstore.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=os.getenv("SECRET_KEY", "bookstore-local-lab-key"),
        MAX_CONTENT_LENGTH=1024 * 1024,
    )

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    from routes.books import books_bp
    app.register_blueprint(books_bp)
    register_errors(app)

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        click.echo("Đã tạo các bảng còn thiếu.")

    @app.cli.command("seed")
    def seed():
        from seed import seed_data
        db.create_all()
        seed_data()
        click.echo("Đã thêm dữ liệu mẫu còn thiếu.")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
