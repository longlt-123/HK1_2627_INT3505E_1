import sqlite3
import hashlib
import json
from urllib.parse import urlencode
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)
# --- CẤU HÌNH ---
DEFAULT_SIZE, MAX_SIZE = 20, 100
app.config['JSON_SORT_KEYS'] = False
BOOKS = []
_next_id = 1

def find(book_id):
    return next((b for b in BOOKS if b["id"] == book_id), None)

# GET/books trả về danh sách sách với tùy biến
@app.get("/books")
def list_books():
    if not BOOKS:
        return jsonify({"data": [], "pagination": None, "_links": {}}), 200

    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", DEFAULT_SIZE))
        limit_str = request.args.get("limit")
        limit = int(limit_str) if limit_str else len(BOOKS)
    except ValueError:
        return jsonify({"error": "page, size, and limit must be integer"}), 400

    page = max(page, 1)
    size = max(min(size, MAX_SIZE), 1)

    result = BOOKS.copy()
    q = request.args.get("q")
    if q:
        result = [b for b in result if q.lower() in b["title"].lower()]

    a = request.args.get("author")
    if a:
        result = [b for b in result if a.lower() == b["author"].lower()]

    result = result[:limit]
    sort_by = request.args.get("sort")
    if sort_by and len(result) > 0:
        if sort_by in result[0]:
            result.sort(key=lambda x: x[sort_by].lower() if isinstance(x[sort_by], str) else x[sort_by])

    total = len(result); start=(page-1)*size; end=start+size
    items = result[start:end]
    last=(total+size-1)//size if total > 0 else 1

    def u(p):
        args = request.args.to_dict()
        args["page"] = p
        args["size"] = size
        return f"/books?{urlencode(args)}"

    links = {
        "self": {"href": u(page)},
        "first": {"href": u(1)}, 
        "last": {"href": u(max(last, 1))}
        }
    if page > 1:
        links["prev"] = {"href": u(page-1)}
    if end < total:
        links["next"] = {"href": u(page+1)}
    
    body = {"data":items,
            "pagination":{"page":page,"size":size,"total":total,"total_pages":last},
            "_links":links
            }
    
    resp = make_response(jsonify(body), 200)
    resp.headers["Cache-Control"]="public, max-age=30"
    return resp

# GET/books/id=... tìm sách theo id
@app.get("/books/<int:bid>")
def get_book(bid):
    book = find(bid)
    if book is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(book), 200

# POST/books bắt buộc có title, author và year phải là int và >= 1900
@app.post("/books")
def create_book():
    global _next_id
    if not request.is_json:
        return jsonify({"error": "expected JSON"}), 415

    body = request.get_json(silent=True) or {}
    t = body.get("title", "")
    a = body.get("author", "")
    y = body.get("year", "unk")
    price = body.get("price", "unk")
    if not t or not a:
        return jsonify({"error": "title and author required"}), 422
    if y != "unk":
        if not isinstance(y, int):
            return jsonify({"error": "year must be integer"}), 409
        if y < 1900:
            return jsonify({"error": "year must be a valid number >= 1900"}), 409

    if price != "unk":
        if not isinstance(price, float):
            return jsonify({"error": "year must be float"}), 409
        if price < 0:
            return jsonify({"error": "price must be a valid number >= 0"}), 409


    book =  {"id": _next_id, "title": t, "author": a, "year": y, "price": price}
    BOOKS.append(book)
    _next_id += 1
    resp = make_response(jsonify(book), 201)
    resp.headers["Location"] = f"/books/{book['id']}"
    return resp

# PUT/book thay toàn bộ, title + author bắt buộc
@app.put("/books/<int:bid>")
def put(bid):
    i = next((k for k,b in enumerate(BOOKS) if b["id"] == bid), None)
    if i is None:
        return jsonify({"error": "not found"}), 404

    body = request.get_json(silent=True) or {}
    t = body.get("title", "")
    a = body.get("author", "")
    y = body.get("year", "unk")
    price = body.get("price", "unk")

    if not t or not a:
        return jsonify({"error": "title and author require"}), 422
    BOOKS[i]={"id":bid,"title":t.strip(),"author":a.strip(), "year": y, "price": price}

    return jsonify(BOOKS[i]), 200

# PATCH chỉ cập nhật field có trong body
@app.patch("/books/<int:bid>")
def patch(bid):
    i = next((k for k,b in enumerate(BOOKS) if b["id"] == bid), None)
    if i is None:
        return jsonify({"error": "not found"}), 404

    body = request.get_json(silent=True) or {}
    t = body.get("title", None)
    a = body.get("author", None)
    y = body.get("year", None)
    price = body.get("price", None)
    
    if t is not None:
        BOOKS[i]["title"] = t
    if a is not None:
        BOOKS[i]["author"] = a
    if y is not None:
        if y < 1900:
            return jsonify({"error": "year must be a valid integer >= 1900"}), 422
        BOOKS[i]["year"] = y
    if price is not None:
        if price < 0:
            return jsonify({"error": "price must be positive"}), 422
        BOOKS[i]["price"] = price
    return jsonify(BOOKS[i]), 200

# DELETE/books/id=... xóa 1 bản ghi theo id
@app.delete("/books/<int:bid>")
def delete(bid):
    i = next((k for k,b in enumerate(BOOKS) if b["id"] == bid), None)
    if i is None:
        return jsonify({"error": "not found"}), 404

    BOOKS.pop(i)
    resp = make_response(jsonify("delete successful"), 204)
    return resp

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)