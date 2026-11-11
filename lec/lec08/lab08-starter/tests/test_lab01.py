"""LAB 1 — add your five tests here. Do not delete the smoke tests.

A. GET /books, empty database -> HTTP 200 and []
B. GET /books/9999 -> HTTP 404, JSON code == NOT_FOUND
C. POST /books with only author -> HTTP 400, errors contains title
D. POST valid book, DELETE it, GET same id -> HTTP 404
BONUS. Validate a Book response using JSON Schema; add an unknown
       field to a *copy* of the response and assert ValidationError.

Useful imports:
    from jsonschema import validate, ValidationError
    import pytest
    from tools import get_book_schema

Do not depend on test execution order. Fixtures: client, app, sample_book.
"""

import pytest
from jsonschema import ValidationError, validate

from tools import get_book_schema


def test_get_books_empty_database_returns_empty_array(client):
    response = client.get("/books")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == []

def test_get_not_found_book(client):
    response = client.get("/books/9999")

    assert response.status_code == 404
    assert response.is_json
    assert response.get_json()["code"] == "NOT_FOUND"

def test_post_book_missing_title_returns_validation_error(client):
    response = client.post("/books", json={"author": "Author Only"})

    assert response.status_code == 400
    assert response.is_json
    errors = response.get_json().get("errors", [])
    assert any(error["field"] == "title" for error in errors)

def test_get_book_after_delete_returns_not_found(client, sample_book):
    # Delete the book
    delete_response = client.delete(f"/books/{sample_book}")
    assert delete_response.status_code == 204

    # Attempt to get the deleted book
    get_response = client.get(f"/books/{sample_book}")
    assert get_response.status_code == 404
    assert get_response.is_json
    assert get_response.get_json()["code"] == "NOT_FOUND"


def test_response_extra_field_blocked(book_response, book_response_with_extra_field):
    schema = get_book_schema()
    schema["properties"]["year"]["type"] = ["integer", "null"]
    schema["properties"]["isbn"]["type"] = ["string", "null"]
    for field in ("year", "isbn"):
        schema["properties"][field].pop("nullable", None)

    assert "password_hash" not in book_response
    validate(instance=book_response, schema=schema)

    with pytest.raises(ValidationError) as exc_info:
        validate(instance=book_response_with_extra_field, schema=schema)

    assert exc_info.value.validator == "additionalProperties"
    assert "password_hash" in exc_info.value.message
