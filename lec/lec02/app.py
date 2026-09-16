from flask import Flask, jsonify, make_response, request

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
BOOKS = []
_next_id = 1

def find(book_id):
    return next((b for b in BOOKS if b["id"] == book_id), None)

# GET/books trả về danh sách sách với tùy biến
@app.get("/books")
def list_books():
    if len(BOOKS) > 0:
        data = BOOKS
    else:
        data = "no book in system"
        return jsonify({"data": data, "total": len(BOOKS)}), 200

    limit = int(request.args.get("limit", 200))
    q = request.args.get("q", "")
    sort_by = str(request.args.get("sort", ""))

    result = [b for b in BOOKS if q in b["title"].lower()] if q else BOOKS[:limit]

    if sort_by:
        result.sort(key=lambda x: x[sort_by].lower() if isinstance(x[sort_by], str) else x[sort_by])

    return jsonify(result[:limit]), 200

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