from flask import Flask, jsonify, request

app = Flask(__name__)

BOOKS = [
    {"id": "1", "name": "Harry Potter"},
    {"id": "2", "name": "Lord of the Rings"}
]

def find_by_id(book_id):
    for b in BOOKS:
        if b["id"] == book_id:
            return b
    return None

# /books/<id> — id là string
@app.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    book = find_by_id(book_id)
    if book is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(book), 200

# Ép kiểu int ngay từ URL
@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    return jsonify({"id": item_id}), 200

@app.route("/books", methods=["GET"])
def list_books():
    limit = int(request.args.get("limit", 20))
    q = request.args.get("q", "").strip().lower()
    
    items = [b for b in BOOKS if q in b["name"].lower()]
    return jsonify({"items": items[:limit]}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)