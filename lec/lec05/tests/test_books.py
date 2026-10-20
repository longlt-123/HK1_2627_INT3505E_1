import pytest
from sqlalchemy.exc import IntegrityError
from models import db, Book, Review, BookAuthor
from pagination import parse_sort, apply_cursor, order_columns
from errors import APIError

BASE = "/api/v1/books"


def payload(**changes):
    return dict(title="Test Book", isbn="TEST-ISBN", price_vnd=100000,
                stock=2, category_id=1, **{}) | changes


def test_crud(client):
    response = client.post(BASE, json=payload())
    assert response.status_code == 201
    location = response.headers["Location"]
    assert client.get(location).json["title"] == "Test Book"
    assert client.patch(location, json={"stock": 8}).json["stock"] == 8
    assert client.put(location, json={"title": "partial"}).status_code == 400
    assert client.put(location, json=payload(title="Replaced")).json["title"] == "Replaced"
    response = client.delete(location)
    assert response.status_code == 204 and response.data == b""
    assert client.get(location).status_code == 404
    assert client.get(location).is_json


@pytest.mark.parametrize("changes", [
    {"category_id": None}, {"category_id": 999}, {"price_vnd": -1},
    {"stock": True}, {"stock": -1}, {"title": " "}, {"title": "x" * 201},
    {"id": 100}, {"isbn": ""}, {"category_id": "1"},
])
def test_invalid_book(client, changes):
    assert client.post(BASE, json=payload(**changes)).status_code == 400


def test_missing_category_and_bad_json(client):
    data = payload()
    del data["category_id"]
    assert client.post(BASE, json=data).status_code == 400
    assert client.post(BASE, data="{", content_type="application/json").status_code == 400
    assert client.post(BASE, data="{}").status_code == 415
    assert client.post(BASE, json=[]).status_code == 400
    assert client.patch(BASE + "/1", json={}).status_code == 400


def test_conflict_rollback(client):
    assert client.post(BASE, json=payload()).status_code == 201
    assert client.post(BASE, json=payload()).status_code == 409
    assert client.post(BASE, json=payload(isbn="UNIQUE")).status_code == 201
    assert client.patch(BASE + "/1", json={"isbn": "UNIQUE"}).status_code == 409
    assert client.get(BASE + "/1").json["isbn"] == "DEMO-0001"


def test_delete_relations(client, app):
    assert client.delete(BASE + "/1").status_code == 204
    with app.app_context():
        assert db.session.scalar(db.select(Review).where(Review.book_id == 1)) is None
        assert db.session.scalar(db.select(BookAuthor).where(BookAuthor.book_id == 1)) is None


def test_database_constraints(app):
    with app.app_context():
        for changes in ({"category_id": 999}, {"price_vnd": -1}, {"stock": -1}):
            db.session.add(Book(**payload(**changes)))
            with pytest.raises(IntegrityError):
                db.session.commit()
            db.session.rollback()


@pytest.mark.parametrize("query", [
    "sort=foo", "sort=price,price", "sort=--price", "sort=", "sort=price,",
    "sort=price;DROP%20TABLE%20books", "limit=0", "limit=101", "limit=abc",
    "limit=-1", "limit=1.5", "offset=-1", "strategy=foo", "genre=",
    "category_id=0", "category_id=abc", "strategy=cursor&offset=0",
    "strategy=offset&cursor=abc", "strategy=cursor&cursor=abc", "strategy=cursor&cursor=",
    "sort=id&sort=price", "unknown=1",
])
def test_bad_queries(client, query):
    response = client.get(BASE + "?" + query)
    assert response.status_code == 400, response.json
    assert response.is_json


def test_offset_and_filter(client):
    response = client.get(BASE + "?strategy=offset&limit=4&offset=4&genre=technology&sort=price")
    body = response.json
    assert body["meta"]["total"] == 10
    assert body["meta"]["next_offset"] == 8
    assert body["meta"]["count"] == 4
    assert all(b["category_id"] == 1 for b in body["data"])
    assert "genre=technology" in body["links"]["next"]
    assert client.get(body["links"]["next"]).json["meta"]["count"] == 2
    assert client.get(BASE + "?genre=missing").json["data"] == []
    assert client.get(BASE + "?genre=technology&category_id=2").json["data"] == []
    empty = client.get(BASE + "?offset=100").json
    assert empty["data"] == [] and empty["links"]["next"] is None


@pytest.mark.parametrize("sort", ["id", "-id", "price", "-price", "-price,title", "title,-stock", "price,-title,id"])
@pytest.mark.parametrize("genre", [None, "technology"])
def test_complete_cursor_traversal(client, sort, genre):
    query = {"strategy": "cursor", "sort": sort, "limit": 3}
    if genre:
        query["genre"] = genre
    all_books = client.get(BASE, query_string={"limit": 100, **({"genre": genre} if genre else {})}).json["data"]
    expected = all_books[:]
    names = {"price": "price_vnd"}
    # Independent Python stable sorting as oracle (not the SQL helper).
    tokens = sort.split(",")
    if not any(t.lstrip("-") == "id" for t in tokens):
        tokens.append("-id" if tokens[-1].startswith("-") else "id")
    for token in reversed(tokens):
        field = names.get(token.lstrip("-"), token.lstrip("-"))
        expected.sort(key=lambda b: b[field], reverse=token.startswith("-"))
    response = client.get(BASE, query_string=query)
    seen = []
    for _ in range(20):
        assert response.status_code == 200
        body = response.json
        seen.extend(b["id"] for b in body["data"])
        if not body["meta"]["has_more"]:
            assert body["meta"]["next_cursor"] is None
            break
        response = client.get(body["links"]["next"])
    else:
        pytest.fail("Cursor did not terminate")
    assert seen == [b["id"] for b in expected]
    assert len(seen) == len(set(seen))


def test_cursor_context_and_tamper(client):
    body = client.get(BASE + "?strategy=cursor&sort=-price&genre=technology&limit=2").json
    token = body["meta"]["next_cursor"]
    for changes in ({"sort": "price"}, {"genre": "fiction"}, {"cursor": token + "x"}):
        query = {"strategy": "cursor", "sort": "-price", "genre": "technology", "cursor": token} | changes
        assert client.get(BASE, query_string=query).status_code == 400


def test_insert_before_cursor_boundary(client):
    body = client.get(BASE + "?strategy=cursor&sort=price&limit=3").json
    first_ids = {b["id"] for b in body["data"]}
    assert client.post(BASE, json=payload(price_vnd=0)).status_code == 201
    next_body = client.get(body["links"]["next"]).json
    assert first_ids.isdisjoint({b["id"] for b in next_body["data"]})


def test_deleted_boundary_still_works(client):
    body = client.get(BASE + "?strategy=cursor&sort=price&limit=3").json
    boundary = body["data"][-1]
    client.delete(BASE + f'/{boundary["id"]}')
    next_body = client.get(body["links"]["next"]).json
    assert len(next_body["data"]) == 3
    assert all((b["price_vnd"], b["id"]) > (boundary["price_vnd"], boundary["id"]) for b in next_body["data"])


def test_helpers(app):
    with pytest.raises(APIError):
        parse_sort("-price,title", allow_multi=False)
    keys = parse_sort("-price", allow_multi=False)
    assert [k.name for k in keys] == ["price", "id"]
    with app.app_context():
        query = apply_cursor(db.select(Book), keys, [75000, 17]).order_by(*order_columns(keys))
        rows = db.session.execute(query).scalars().all()
        assert rows
        assert all((b.price_vnd, b.id) < (75000, 17) for b in rows)


def test_seed_idempotent(app):
    from seed import seed_data
    with app.app_context():
        seed_data()
        assert db.session.query(Book).count() == 30
