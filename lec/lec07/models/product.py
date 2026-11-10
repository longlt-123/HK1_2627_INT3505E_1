from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db


class Product(db.Model):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price_cents >= 0", name="ck_products_price_nonnegative"),
        CheckConstraint("qty_in_stock >= 0", name="ck_products_stock_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(2000))
    price_cents: Mapped[int] = mapped_column(Integer)
    qty_in_stock: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    archived: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=db.false(), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
