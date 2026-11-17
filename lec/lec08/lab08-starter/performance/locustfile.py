"""Lab 4: weighted tasks and 1% client-side simulated failures on year searches.

The injected failure is NOT an HTTP 500 returned by Flask.
Set LOCUST_FAKE_FAILURE_RATE=0 to disable injection for a CI baseline.
"""
import itertools
import os
import random

from locust import HttpUser, between, task

_counter = itertools.count(1)
YEARS = (2017, 2021, 2024)
FAKE_FAILURE_RATE = float(os.environ.get("LOCUST_FAKE_FAILURE_RATE", "0.01"))
if not 0 <= FAKE_FAILURE_RATE <= 1:
    raise ValueError("LOCUST_FAKE_FAILURE_RATE must be between 0 and 1")


class BooksUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_books(self):
        self.client.get("/books", name="GET /books")

    @task(2)
    def read_book(self):
        book_id = random.randint(1, 50)
        with self.client.get(
            f"/books/{book_id}", name="GET /books/{id}", catch_response=True
        ) as response:
            # Expected 404 (random id absent) is not an operational failure.
            if response.status_code in (200, 404):
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}")

    @task(1)
    def create_book(self):
        unique = next(_counter)
        self.client.post(
            "/books",
            json={
                "title": f"Load test {unique}",
                "author": "locust",
                "year": random.choice(YEARS),
            },
            name="POST /books",
        )

    @task(1)
    def search_by_year(self, year=None):
        # Locust invokes tasks without arguments; callers may supply a year.
        year = random.choice(YEARS) if year is None else year
        with self.client.get(
            "/books",
            params={"year": year},
            name="GET /books?year={year}",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Year search: unexpected HTTP {response.status_code}")
                return
            try:
                books = response.json()
            except ValueError:
                response.failure("Year search: response is not JSON")
                return
            if not isinstance(books, list) or any(
                not isinstance(book, dict) or book.get("year") != year
                for book in books
            ):
                response.failure("Year search: expected an array of books matching the year")
            elif random.random() < FAKE_FAILURE_RATE:
                response.failure("Injected failure: simulated 500 (client-side; actual HTTP 200)")
