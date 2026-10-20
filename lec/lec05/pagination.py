from dataclasses import dataclass
from flask import current_app, request, url_for
from itsdangerous import URLSafeSerializer, BadData
from sqlalchemy import and_, or_
from errors import APIError
from models import Book

SORT = {"id": Book.id, "price": Book.price_vnd, "title": Book.title, "stock": Book.stock}
MAX_ID = 2147483647


@dataclass(frozen=True)
class SortKey:
    name: str
    desc: bool

    @property
    def column(self):
        return SORT[self.name]


def parse_sort(raw, *, allow_multi=True):
    """Lab 2: allow_multi=False. Bài tập 2: mặc định hỗ trợ nhiều khóa."""
    tokens = raw.split(",")
    if not allow_multi and len(tokens) != 1:
        raise APIError("bad_sort", "Lab 2 chỉ hỗ trợ một khóa sort.")
    
    result, seen = [], set()
    for token in tokens:
        desc = token.startswith("-")
        key = token[1:] if desc else token
        if key not in SORT or key in seen:
            raise APIError("bad_sort", "Sort không hợp lệ hoặc trùng khóa: " + token)
        result.append(SortKey(key, desc))
        seen.add(key)

    if "id" not in seen:
        result.append(SortKey("id", result[-1].desc))
    return result


def sort_signature(keys):
    return [("-" if key.desc else "") + key.name for key in keys]


def order_columns(keys):
    return [key.column.desc() if key.desc else key.column.asc() for key in keys]


def parse_integer(raw, name, minimum=0, maximum=MAX_ID):
    if not isinstance(raw, str) or not raw.isascii() or not raw.isdecimal() or len(raw) > 10:
        raise APIError("bad_parameter", f"{name} phải là số nguyên từ {minimum} đến {maximum}.")
    
    value = int(raw)
    if not minimum <= value <= maximum:
        raise APIError("bad_parameter", f"{name} phải từ {minimum} đến {maximum}.")
    
    return value


def serializer():
    return URLSafeSerializer(current_app.config["SECRET_KEY"], salt="book-list-v1")


def encode_cursor(book, keys, filters):
    return serializer().dumps({"v": 1, "sort": sort_signature(keys), "filters": filters,
                               "values": [getattr(book, key.column.key) for key in keys]})


def decode_cursor(token, keys, filters):
    try:
        if not token or len(token) > 4096:
            raise ValueError()
        
        payload = serializer().loads(token)
        if not isinstance(payload, dict) or payload.get("v") != 1:
            raise ValueError()
        
        if payload.get("sort") != sort_signature(keys) or payload.get("filters") != filters:
            raise ValueError()
        
        values = payload.get("values")
        if not isinstance(values, list) or len(values) != len(keys):
            raise ValueError()
        
        for key, value in zip(keys, values):
            if key.name == "title":
                if not isinstance(value, str) or not 1 <= len(value) <= 200:
                    raise ValueError()
            elif type(value) is not int or not (1 if key.name == "id" else 0) <= value <= MAX_ID:
                raise ValueError()
            
        return values
    except (BadData, ValueError, TypeError):
        raise APIError("bad_cursor", "Cursor không hợp lệ hoặc không khớp sort/filter.") from None


def apply_cursor(query, keys, values):
    # (a > A) OR (a = A AND b < B) OR (... AND id > ID), tùy chiều từng khóa.
    branches = []
    for index, key in enumerate(keys):
        prefix = [keys[j].column == values[j] for j in range(index)]
        comparison = key.column < values[index] if key.desc else key.column > values[index]
        branches.append(and_(*prefix, comparison))
    return query.where(or_(*branches))


def build_response(rows, limit, strategy, keys, filters, *, offset=0, total=None):
    has_more = len(rows) > limit
    items = rows[:limit]
    token = encode_cursor(items[-1], keys, filters) if has_more and strategy == "cursor" else None
    next_offset = offset + limit if has_more and strategy == "offset" else None
    next_url = None

    if has_more:
        args = request.args.to_dict()
        args.update(strategy=strategy, limit=limit)
        args.pop("cursor", None)
        args.pop("offset", None)
        args["cursor" if strategy == "cursor" else "offset"] = token if strategy == "cursor" else next_offset
        next_url = url_for("books.list_books", **args)
        
    meta = {"strategy": strategy, "limit": limit, "count": len(items), "has_more": has_more,
            "sort": sort_signature(keys), "next_cursor": token, "next_offset": next_offset}
    if strategy == "offset":
        meta.update(offset=offset, total=total)
    return {"data": [book.to_dict() for book in items], "meta": meta, "links": {"next": next_url}}
