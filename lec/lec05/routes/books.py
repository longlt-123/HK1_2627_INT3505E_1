import json
from pathlib import Path
from flask import Blueprint, request, jsonify
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError
from models import db, Book

books_bp = Blueprint("books", __name__, url_prefix="/api/v1/books")

schema_path = Path(__file__).resolve().parent.parent / "schemas" / "book.json"
book_schema = json.loads(schema_path.read_text(encoding="utf-8"))

@books_bp.route("", methods=["GET"])
def get_books():
    books = db.session.execute(db.select(Book)).scalars().all()
    return jsonify([book.to_dict() for book in books]), 200

@books_bp.route("/<int:id>", methods=["GET"])
def get_book(id):
    book = db.get_or_404(Book, id)
    return jsonify(book.to_dict()), 200

@books_bp.route("", methods=["POST"])
def create_book():
    data = request.get_json(silent=True)
    try:
        validate(data, book_schema)
    except ValidationError as e:
        return jsonify({"error": e.message}), 400

    book = Book(**data)
    db.session.add(book)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error"}), 409

    return jsonify(book.to_dict()), 201

@books_bp.route("/<int:id>", methods=["PUT", "PATCH"])
def update_book(id):
    book = db.get_or_404(Book, id)
    data = request.get_json(silent=True)

    schema = book_schema.copy()
    if request.method == "PATCH":
        schema["required"] = []

    try:
        validate(data, schema)
    except ValidationError as e:
        return jsonify({"error": e.message}), 400

    for key, value in data.items():
        setattr(book, key, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error"}), 409

    return jsonify(book.to_dict())


@books_bp.route("/<int:id>", methods=["DELETE"])
def delete_book(id):
    book = db.get_or_404(Book, id)
    db.session.delete(book)
    db.session.commit()
    return "", 204