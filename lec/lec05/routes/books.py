import json
from pathlib import Path
from flask import Blueprint, request, jsonify, url_for
from jsonschema import Draft202012Validator
from sqlalchemy import func
from errors import APIError
from models import db, Book, Category
from pagination import (parse_sort, order_columns, parse_integer, decode_cursor,
                        apply_cursor, build_response)

books_bp = Blueprint("books", __name__, url_prefix="/api/v1/books")
book_schema = json.loads((Path(__file__).resolve().parent.parent / "schemas" / "book.json").read_text(encoding="utf-8"))
Draft202012Validator.check_schema(book_schema)


def valid_body(partial=False):
    data = request.get_json()
    schema = dict(book_schema)
    if partial:
        schema["required"] = []
        schema["minProperties"] = 1
    errors = list(Draft202012Validator(schema).iter_errors(data))
    if errors:
        raise APIError("validation_error", errors[0].message)
    if "category_id" in data and db.session.get(Category, data["category_id"]) is None:
        raise APIError("invalid_category", "category_id không tồn tại.")
    return data


@books_bp.get("")
def list_books():
    allowed = {"strategy", "sort", "limit", "offset", "cursor", "genre", "category_id"}

    if set(request.args) - allowed or any(len(request.args.getlist(k)) != 1 for k in request.args):
        raise APIError("bad_parameter", "Query parameter không hỗ trợ hoặc bị lặp.")
    
    strategy = request.args.get("strategy", "offset")
    if strategy not in ("offset", "cursor"):
        raise APIError("bad_strategy", "strategy phải là offset hoặc cursor.")
    
    if (strategy == "offset" and "cursor" in request.args) or (strategy == "cursor" and "offset" in request.args):
        raise APIError("bad_parameter", "Không trộn offset với cursor.")
    
    limit = parse_integer(request.args.get("limit", "20"), "limit", 1, 100)
    keys = parse_sort(request.args.get("sort", "id"))
    category_id = None

    if "category_id" in request.args:
        category_id = parse_integer(request.args["category_id"], "category_id", 1)
    
    genre = request.args.get("genre")

    if genre is not None and (not genre.strip() or len(genre) > 100):
        raise APIError("bad_parameter", "genre phải là slug thể loại, dài 1–100 ký tự.")
    
    filters = {"category_id": category_id, "genre": genre}
    query = db.select(Book)

    if category_id is not None:
        query = query.where(Book.category_id == category_id)

    if genre is not None:
        query = query.join(Book.category).where(Category.slug == genre)

    offset, total = 0, None
    if strategy == "offset":
        offset = parse_integer(request.args.get("offset", "0"), "offset")
        total = db.session.scalar(db.select(func.count()).select_from(query.subquery()))
        query = query.offset(offset)
    elif strategy == "cursor" and "cursor" in request.args:
        query = apply_cursor(query, keys, decode_cursor(request.args["cursor"], keys, filters))

    rows = db.session.execute(query.order_by(*order_columns(keys)).limit(limit + 1)).scalars().all()
    return jsonify(build_response(rows, limit, strategy, keys, filters, offset=offset, total=total))


@books_bp.get("/<int:id>")
def get_book(id):
    return jsonify(db.get_or_404(Book, id).to_dict())


@books_bp.post("")
def create_book():
    book = Book(**valid_body())
    db.session.add(book)
    db.session.commit()
    return jsonify(book.to_dict()), 201, {"Location": url_for("books.get_book", id=book.id)}


@books_bp.route("/<int:id>", methods=["PUT", "PATCH"])
def update_book(id):
    book = db.get_or_404(Book, id)
    for key, value in valid_body(partial=request.method == "PATCH").items():
        setattr(book, key, value)
    db.session.commit()
    return jsonify(book.to_dict())


@books_bp.delete("/<int:id>")
def delete_book(id):
    book = db.get_or_404(Book, id)
    db.session.delete(book)
    db.session.commit()
    return "", 204
