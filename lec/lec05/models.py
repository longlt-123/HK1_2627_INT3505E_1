import sqlite3
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, CheckConstraint, Index
from sqlalchemy.engine import Engine
from sqlalchemy.orm import mapped_column, relationship

db = SQLAlchemy()


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(connection, _):
    if isinstance(connection, sqlite3.Connection):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class Book(db.Model):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("price_vnd >= 0", name="ck_book_price"),
        CheckConstraint("stock >= 0", name="ck_book_stock"),
        Index("ix_books_price_id", "price_vnd", "id"),
        Index("ix_books_category_price_id", "category_id", "price_vnd", "id"),
    )
    id = mapped_column(db.Integer, primary_key=True)
    title = mapped_column(db.String(200), nullable=False)
    isbn = mapped_column(db.String(20), nullable=False, unique=True)
    price_vnd = mapped_column(db.Integer, nullable=False)
    stock = mapped_column(db.Integer, default=0, nullable=False)
    category_id = mapped_column(db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True)
    category = relationship("Category", back_populates="books")
    authors = relationship("Author", secondary="book_authors", back_populates="books")
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")

    def to_dict(self):
        return {key: getattr(self, key) for key in
                ("id", "title", "isbn", "price_vnd", "stock", "category_id")}


class BookAuthor(db.Model):
    __tablename__ = "book_authors"
    book_id = mapped_column(db.Integer, db.ForeignKey("books.id", ondelete="CASCADE"), primary_key=True)
    author_id = mapped_column(db.Integer, db.ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True)


class Category(db.Model):
    __tablename__ = "categories"
    id = mapped_column(db.Integer, primary_key=True)
    name = mapped_column(db.String(100), nullable=False)
    slug = mapped_column(db.String(100), unique=True, nullable=False)
    books = relationship("Book", back_populates="category")


class Author(db.Model):
    __tablename__ = "authors"
    id = mapped_column(db.Integer, primary_key=True)
    name = mapped_column(db.String(100), nullable=False)
    bio = mapped_column(db.Text)
    books = relationship("Book", secondary="book_authors", back_populates="authors")


class User(db.Model):
    __tablename__ = "users"
    id = mapped_column(db.Integer, primary_key=True)
    email = mapped_column(db.String(100), unique=True, nullable=False)
    display_name = mapped_column(db.String(100))
    reviews = relationship("Review", back_populates="user")


class Review(db.Model):
    __tablename__ = "reviews"
    __table_args__ = (CheckConstraint("rating BETWEEN 1 AND 5", name="ck_review_rating"),)
    id = mapped_column(db.Integer, primary_key=True)
    rating = mapped_column(db.Integer, nullable=False)
    book_id = mapped_column(db.Integer, db.ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    user_id = mapped_column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book = relationship("Book", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
