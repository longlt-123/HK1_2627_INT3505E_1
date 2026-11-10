from flask import abort, request


def json_body():
    if not request.is_json:
        abort(400, description="Content-Type must be application/json")
    return request.get_json()


def pagination():
    try:
        page = max(1, int(request.args.get("page", 1)))
        size = min(100, max(1, int(request.args.get("size", 20))))
    except ValueError:
        abort(400, description="page and size must be integers")
    return page, size
