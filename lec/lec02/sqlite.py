import sqlite3
import hashlib
import json
from urllib.parse import urlencode
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

# --- CẤU HÌNH ---
DEFAULT_SIZE, MAX_SIZE = 20, 100
DB_FILE = 'database.db'

# --- HÀM HỖ TRỢ ---
def generate_etag(data_dict):
    """ Hàm tạo mã băm (hash) theo nội dung của dữ liệu """
    clean_data = {k: v for k, v in data_dict.items() if k not in ('id', 'etag')}

    return hashlib.md5(json.dumps(clean_data, sort_keys=True).encode('utf-8')).hexdigest()

def get_db_connection():
    """ Kết nối SQLite và format row thành dạng Dictionary """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    """ Khởi tạo database, tạo bảng và thêm dữ liệu mẫu nếu DB trống """
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    author TEXT,
                    year INTEGER,
                    price REAL,
                    etag TEXT
                )''')
                
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT,
                    total_amount REAL
                )''')

    c.execute("SELECT COUNT(*) FROM books")
    if c.fetchone()[0] == 0:
        sample_books = [
            {"title": "Clean Code", "author": "R. Martin", "year": 2008, "price": 34.49},
            {"title": "Pragmatic Programmer", "author": "Andy Hunt", "year": 1999, "price": 39.99}
        ]
        for b in sample_books:
            etag = generate_etag(b)
            c.execute("INSERT INTO books (title, author, year, price, etag) VALUES (?, ?, ?, ?, ?)",
                      (b['title'], b['author'], b['year'], b['price'], etag))
        
        c.execute("INSERT INTO orders (customer_name, total_amount) VALUES ('John Doe', 74.48)")
        c.execute("INSERT INTO orders (customer_name, total_amount) VALUES ('Jane Smith', 120.00)")
        
    conn.commit()
    conn.close()

init_db()


@app.get("/books")
def list_books():
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", DEFAULT_SIZE))
        limit_str = request.args.get("limit")
        limit = int(limit_str) if limit_str else None
    except ValueError:
        return jsonify({"error": "page, size, and limit must be integer"}), 400

    page = max(page, 1)
    size = max(min(size, MAX_SIZE), 1)

    conn = get_db_connection()
    c = conn.cursor()

    where_clauses = []
    params = []
    
    q = request.args.get("q")
    if q:
        where_clauses.append("LOWER(title) LIKE ?")
        params.append(f"%{q.lower()}%")
        
    a = request.args.get("author")
    if a:
        where_clauses.append("LOWER(author) = ?")
        params.append(a.lower())

    where_sql = " AND ".join(where_clauses)
    if where_sql:
        where_sql = "WHERE " + where_sql

    sort_by = request.args.get("sort")
    sort_sql = ""
    valid_cols = ["id", "title", "author", "year", "price"]
    if sort_by and sort_by in valid_cols:
        sort_sql = f"ORDER BY {sort_by}"

    limit_sql = ""
    if limit is not None:
        limit_sql = "LIMIT ?"
        params.append(limit)

    base_query = f"SELECT * FROM books {where_sql} {sort_sql} {limit_sql}"

    c.execute(f"WITH CTE AS ({base_query}) SELECT COUNT(*) FROM CTE", params)
    total = c.fetchone()[0]

    # Tính toán biến phân trang
    start = (page - 1) * size
    end = start + size
    last = (total + size - 1) // size if total > 0 else 1

    c.execute(f"WITH CTE AS ({base_query}) SELECT * FROM CTE LIMIT ? OFFSET ?", params + [size, start])
    rows = c.fetchall()
    conn.close()
    
    items = []
    for row in rows:
        book_dict = dict(row)
        book_dict.pop('etag', None)
        items.append(book_dict)

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
        links["prev"] = {"href": u(page - 1)}
    if end < total:
        links["next"] = {"href": u(page + 1)}

    # 6. RESPONSE
    body = {
        "data": items,
        "pagination": {"page": page, "size": size, "total": total, "total_pages": last},
        "_links": links
    }

    resp = make_response(jsonify(body), 200)
    resp.headers["Cache-Control"] = "public, max-age=30"
    return resp

@app.get("/books/<int:book_id>")
def get_book(book_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "not found"}), 404

    book = dict(row)
    
    etag = book.pop("etag") 

    if_none_match = request.headers.get("If-None-Match")
    if if_none_match == etag:
        return '', 304

    resp = make_response(jsonify(book), 200)
    resp.headers["ETag"] = etag
    return resp

@app.get("/orders/<int:oid>")
def get_order(oid):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE id = ?", (oid,))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "order not found"}), 404

    return jsonify(dict(row)), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)