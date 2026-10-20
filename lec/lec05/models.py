from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import mapped_column, relationship
db = SQLAlchemy()

class Book(db.Model):
    __tablename__ = "books"

    id = mapped_column(db.Integer, primary_key=True)
    title = mapped_column(db.String(200), nullable=False)
    isbn = mapped_column(db.String(20), nullable=False, unique=True)
    price_vnd = mapped_column(db.Integer, nullable=False)
    stock = mapped_column(db.Integer, default=0, nullable=False)
    category_id = mapped_column(db.Integer, db.ForeignKey("categories.id"),nullable=False)

    category = relationship("Category", back_populates="books")
    authors = relationship("Author", secondary="book_authors", back_populates="books")
    reviews = relationship("Review", back_populates="book")
    

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "isbn": self.isbn,
            "price_vnd": self.price_vnd,
            "stock": self.stock,
            "category_id": self.category_id
        }

class BookAuthor(db.Model):
    __tablename__ = "book_authors"

    book_id = mapped_column(db.Integer, db.ForeignKey("books.id"), primary_key=True)
    author_id = mapped_column(db.Integer, db.ForeignKey("authors.id"), primary_key=True)


class Category(db.Model):
    __tablename__ = "categories"

    id = mapped_column(db.Integer, primary_key=True)
    name = mapped_column(db.String(100), nullable=False)
    slug = mapped_column(db.String(100), unique=True)

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

    id = mapped_column(db.Integer, primary_key=True)
    rating = mapped_column(db.Integer, nullable=False)
    book_id = mapped_column(db.Integer, db.ForeignKey("books.id"),nullable=False)
    user_id = mapped_column(db.Integer, db.ForeignKey("users.id"),nullable=False)

    book = relationship("Book", back_populates="reviews")
    user = relationship("User", back_populates="reviews")