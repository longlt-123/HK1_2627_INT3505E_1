from models import db, Book, Category, Author, User, Review


def seed_data():
    categories = []
    for name, slug in [("Công nghệ", "technology"), ("Tiểu thuyết", "fiction"), ("Khoa học", "science")]:
        category = db.session.scalar(db.select(Category).where(Category.slug == slug))
        if category is None:
            category = Category(name=name, slug=slug)
            db.session.add(category)
        categories.append(category)
    author = db.session.scalar(db.select(Author).where(Author.name == "Tác giả mẫu"))
    if author is None:
        author = Author(name="Tác giả mẫu", bio="Dữ liệu giả phục vụ bài lab")
        db.session.add(author)
    user = db.session.scalar(db.select(User).where(User.email == "student@example.com"))
    if user is None:
        user = User(email="student@example.com", display_name="Student")
        db.session.add(user)
    db.session.flush()
    for i in range(1, 31):
        isbn = f"DEMO-{i:04d}"
        if db.session.scalar(db.select(Book).where(Book.isbn == isbn)) is None:
            book = Book(title=f"Sach mau {i % 5 + 1}", isbn=isbn,
                        price_vnd=50000 + (i % 4) * 25000, stock=i % 7,
                        category=categories[(i - 1) % 3], authors=[author])
            db.session.add(book)
            if i == 1:
                db.session.add(Review(rating=5, book=book, user=user))
    db.session.commit()
