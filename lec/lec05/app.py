from flask import Flask
from models import db
from routes.books import books_bp

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bookstore.db"

db.init_app(app)
app.register_blueprint(books_bp)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)