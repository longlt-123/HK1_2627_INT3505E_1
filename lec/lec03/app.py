from flask import Flask, request, jsonify
from errors import (
    CreatePostProblem,
    GetPostDetailProblem,
    GetPostCommentsProblem
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

@app.errorhandler(CreatePostProblem)
@app.errorhandler(GetPostDetailProblem)
@app.errorhandler(GetPostCommentsProblem)
def handle_problem(error):
    response = jsonify({
        "type": error.type_path,
        "title": error.title,
        "detail": error.detail,
        "instance": error.instance_path,
        "status": error.status
    })

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


if __name__ == '__main__':
    app.run(debug=True, port=5000)