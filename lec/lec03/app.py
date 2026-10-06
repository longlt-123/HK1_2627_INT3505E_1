import base64
import binascii
import json

from flask import Flask, request, jsonify, url_for
from errors import (
    APIProblem,
    CreatePostProblem,
    GetPostDetailProblem,
    GetPostCommentsProblem,
    InvalidCursorProblem,
    InvalidOrderQueryProblem
)

app = Flask(__name__)

USERS = [
    {"id": 1, "name": "R. Martin", "following": [2, 3]},
    {"id": 2, "name": "Fowler", "following": []}
]

POSTS = [
    {"id": 1, "author_id": 1, "title": "REST API", "content": "Design guidelines...", "tags": ["rest"]}
]

COMMENTS = [
    {"id": 1, "post_id": 1, "author_id": 2, "content": "Hello everyone!!!"}
]

ORDERS = [
    {"id": 1, "customer_id": 101, "status": "paid", "total": 120.50, "created_at": "2026-10-01T08:30:00Z"},
    {"id": 2, "customer_id": 102, "status": "pending", "total": 75.00, "created_at": "2026-10-01T09:15:00Z"},
    {"id": 3, "customer_id": 101, "status": "shipped", "total": 230.00, "created_at": "2026-10-02T10:00:00Z"},
    {"id": 4, "customer_id": 103, "status": "paid", "total": 49.99, "created_at": "2026-10-02T11:45:00Z"},
    {"id": 5, "customer_id": 104, "status": "cancelled", "total": 310.00, "created_at": "2026-10-03T12:00:00Z"},
    {"id": 6, "customer_id": 102, "status": "paid", "total": 99.90, "created_at": "2026-10-03T14:20:00Z"},
    {"id": 7, "customer_id": 105, "status": "pending", "total": 150.75, "created_at": "2026-10-04T08:10:00Z"},
    {"id": 8, "customer_id": 101, "status": "paid", "total": 450.00, "created_at": "2026-10-04T09:30:00Z"},
    {"id": 9, "customer_id": 103, "status": "shipped", "total": 88.80, "created_at": "2026-10-05T10:40:00Z"},
    {"id": 10, "customer_id": 104, "status": "paid", "total": 64.25, "created_at": "2026-10-05T16:00:00Z"},
    {"id": 11, "customer_id": 105, "status": "pending", "total": 199.99, "created_at": "2026-10-06T08:00:00Z"},
    {"id": 12, "customer_id": 102, "status": "paid", "total": 520.00, "created_at": "2026-10-06T09:10:00Z"},
]

ORDER_FIELDS = {"id", "customer_id", "status", "total", "created_at"}
ORDER_SORT_FIELDS = {"id", "customer_id", "status", "total", "created_at"}

@app.errorhandler(APIProblem)
def handle_problem(error):
    response = jsonify(error.to_dict())
    response.content_type = "application/problem+json"
    return response, error.status

@app.route('/api/v1/posts', methods=['GET'])
def get_posts():
    """Lấy danh sách tất cả bài viết"""

    author_id = request.args.get('author_id', type=int)
    if author_id:
        filtered_posts = [
            p for p in POSTS
            if p.get('author_id') == author_id
        ]

        return jsonify(filtered_posts), 200

    return jsonify(POSTS), 200


@app.route('/api/v1/posts', methods=['POST'])
def create_post():
    """Tạo bài viết mới"""

    data = request.get_json(silent=True)
    if not data:
        raise CreatePostProblem(
            detail="Request body must contain valid JSON."
        )

    missing_fields = []

    if 'author_id' not in data:
        missing_fields.append('author_id')

    if 'title' not in data:
        missing_fields.append('title')

    if 'content' not in data:
        missing_fields.append('content')

    if missing_fields:
        raise CreatePostProblem(
            detail="Missing required fields: "
                   + ", ".join(missing_fields)
        )

    new_id = POSTS[-1]['id'] + 1 if POSTS else 1

    new_post = {
        "id": new_id,
        "author_id": data['author_id'],
        "title": data['title'],
        "content": data['content'],
        "tags": data.get('tags', [])
    }

    POSTS.append(new_post)

    return jsonify(new_post), 201


@app.route('/api/v1/posts/<int:post_id>', methods=['GET'])
def get_post_detail(post_id):
    """Lấy chi tiết một bài viết"""

    post = next(
        (p for p in POSTS if p['id'] == post_id),
        None
    )
    if post is None:
        raise GetPostDetailProblem(post_id)

    return jsonify(post), 200


@app.route('/api/v1/posts/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    """Lấy danh sách bình luận của một bài viết"""

    post = next(
        (p for p in POSTS if p['id'] == post_id),
        None
    )

    if post is None:
        raise GetPostCommentsProblem(post_id)

    post_comments = [
        c for c in COMMENTS
        if c['post_id'] == post_id
    ]
    return jsonify(post_comments), 200

def encode_cursor(order, sort_expression):
    """Tạo opaque cursor từ item cuối của trang hiện tại."""
    sort_field = sort_expression.lstrip("-")

    payload = {
        "id": order["id"],
        "sort": sort_expression,
        "value": order[sort_field]
    }

    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def decode_cursor(cursor, sort_expression, instance_path):
    """Giải mã và kiểm tra cursor."""
    try:
        padding = "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode((cursor + padding).encode("utf-8"))
        payload = json.loads(raw.decode("utf-8"))

        if not isinstance(payload, dict):
            raise ValueError

        if set(payload.keys()) != {"id", "sort", "value"}:
            raise ValueError

        if payload["sort"] != sort_expression:
            raise ValueError

        if not isinstance(payload["id"], int):
            raise ValueError

        return payload

    except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError, binascii.Error):
        raise InvalidCursorProblem(instance_path)


def apply_sparse_fields(order, requested_fields):
    if requested_fields is None:
        return order.copy()

    return {
        field: order[field]
        for field in requested_fields
    }


@app.route('/api/v1/orders', methods=['GET'])
def get_orders():
    """
    - cursor pagination: ?limit=5&cursor=...
    - filter: ?status=paid&customer_id=101
    - sort: ?sort=total hoặc ?sort=-total
    - sparse fieldsets: ?fields=id,total
    """

    instance_path = request.full_path.rstrip("?")

    # 1. limit
    limit_raw = request.args.get("limit", "5")

    try:
        limit = int(limit_raw)
    except ValueError:
        raise InvalidOrderQueryProblem(
            detail="limit must be an integer.",
            instance_path=instance_path
        )

    if limit < 1 or limit > 100:
        raise InvalidOrderQueryProblem(
            detail="limit must be between 1 and 100.",
            instance_path=instance_path
        )

    # 2. filter
    status = request.args.get("status")
    customer_id_raw = request.args.get("customer_id")

    customer_id = None
    if customer_id_raw is not None:
        try:
            customer_id = int(customer_id_raw)
        except ValueError:
            raise InvalidOrderQueryProblem(
                detail="customer_id must be an integer.",
                instance_path=instance_path
            )

    orders = ORDERS[:]

    if status is not None:
        orders = [
            order for order in orders
            if order["status"] == status
        ]

    if customer_id is not None:
        orders = [
            order for order in orders
            if order["customer_id"] == customer_id
        ]

    # 3. sort
    sort_expression = request.args.get("sort", "id")
    descending = sort_expression.startswith("-")
    sort_field = sort_expression.lstrip("-")

    if sort_field not in ORDER_SORT_FIELDS:
        raise InvalidOrderQueryProblem(
            detail=(
                f"Unsupported sort field '{sort_field}'. "
                f"Allowed fields: {', '.join(sorted(ORDER_SORT_FIELDS))}."
            ),
            instance_path=instance_path
        )

    if sort_field == "id":
        orders.sort(
            key=lambda order: order["id"],
            reverse=descending
        )
    else:
        orders.sort(
            key=lambda order: (order[sort_field], order["id"]),
            reverse=descending
        )

    # 4. sparse fieldsets
    fields_raw = request.args.get("fields")
    requested_fields = None

    if fields_raw is not None:
        requested_fields = [
            field.strip()
            for field in fields_raw.split(",")
            if field.strip()
        ]

        if not requested_fields:
            raise InvalidOrderQueryProblem(
                detail="fields must contain at least one field.",
                instance_path=instance_path
            )

        invalid_fields = [
            field for field in requested_fields
            if field not in ORDER_FIELDS
        ]

        if invalid_fields:
            raise InvalidOrderQueryProblem(
                detail=(
                    f"Unsupported fields: {', '.join(invalid_fields)}. "
                    f"Allowed fields: {', '.join(sorted(ORDER_FIELDS))}."
                ),
                instance_path=instance_path
            )

    # 5. cursor pagination
    cursor = request.args.get("cursor")
    start_index = 0

    if cursor:
        payload = decode_cursor(
            cursor,
            sort_expression,
            instance_path
        )

        cursor_index = next(
            (
                index
                for index, order in enumerate(orders)
                if order["id"] == payload["id"]
                and order[sort_field] == payload["value"]
            ),
            None
        )

        if cursor_index is None:
            raise InvalidCursorProblem(instance_path)

        start_index = cursor_index + 1

    page = orders[start_index:start_index + limit]

    has_more = start_index + limit < len(orders)

    next_cursor = None
    if page and has_more:
        next_cursor = encode_cursor(
            page[-1],
            sort_expression
        )

    response_data = [
        apply_sparse_fields(order, requested_fields)
        for order in page
    ]

    return jsonify({
        "data": response_data,
        "pagination": {
            "limit": limit,
            "next_cursor": next_cursor,
            "has_more": has_more
        }
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)