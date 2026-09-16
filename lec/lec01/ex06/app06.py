from flask import Flask, jsonify, request

app = Flask(__name__)
_next = 2
BOOKS = [
    {"id":1, "title":"Clean Code", "author":"R. Martin", "year": 2008}
]

def find(book_id):
    return next((b for b in BOOKS if b["id"] == book_id), None)

# DETAIL — GET /books/<int:id>
@app.route("/books/<int:book_id>", methods=["GET"])
def get_book(book_id):
    book = find(book_id)
    if book is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(book), 200

# LIST — GET /books
@app.route("/books", methods=["GET"])
def list_books():
    limit = int(request.args.get("limit", 100))
    q = request.args.get("q", "").strip().lower()
    sort_by = request.args.get("q", "").strip().lower()

    result = [b for b in BOOKS if q in b["title"].lower()] if q else BOOKS[:limit]

    if sort_by == "title":
        result.sort(key=lambda x: x["title"].lower())

    return jsonify(result[:limit]), 200

# CREATE — POST /books
@app.route("/books", methods=["POST"])
def create_book():
    global _next
    body = request.get_json(silent=True) or {}
    t, a, year = body.get("title", ""), body.get("author", ""), book.year("year", 0)
    if not t or not a or not year:
        return {"error":"need title + author + year"}, 400
    try:
        year_val = int(year)
        if year_val < 1900:
            return {"error": "year must be >= 1900"}, 400
    except (ValueError, TypeError):
        return {"error": "year must be a valid number >= 1900"}, 400
    
    book = {"id": _next, "title": t, "author": a, "year": year_val}

    _next += 1
    BOOKS.append(book)
    return jsonify(book), 201, {"Location":f"/books/{book['id']}"}

# UPDATE — PUT, DELETE — DELETE
@app.route("/books/<int:book_id>", methods=["PUT", "DELETE"])
def modify_book(book_id):
    book = find(book_id)
    if not book:
        return {"error":"not found"}, 404
    
    if request.method == "PUT":
        body = request.get_json(silent=True) or {}
        if "year" in body:
            try:
                year_val = int(body["year"])
                if year_val < 1900:
                    return {"error": "year must be >= 1900"}, 400
                body["year"] = year_val
            except (ValueError, TypeError):
                return {"error": "year must be a valid number >= 1900"}, 400
                
        book.update(body)
        return jsonify(book), 200
    
    BOOKS.remove(book)
    return "", 204

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)