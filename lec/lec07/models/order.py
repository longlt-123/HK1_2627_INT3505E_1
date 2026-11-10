from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .product import Product


class Order(db.Model):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan",
        lazy="raise", order_by="OrderItem.id"
    )

    @property
    def total_cents(self):
        return sum(item.subtotal_cents for item in self.items)


class OrderItem(db.Model):
    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint("order_id", "product_id", name="uq_order_items_product"),
        CheckConstraint("qty > 0", name="ck_order_items_qty_positive"),
        CheckConstraint("unit_price_cents >= 0", name="ck_order_items_price_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    qty: Mapped[int] = mapped_column(Integer)
    # Snapshot the price so later product edits cannot change the order total.
    unit_price_cents: Mapped[int] = mapped_column(Integer)
    order: Mapped[Order] = relationship(back_populates="items", lazy="raise")
    product: Mapped[Product] = relationship(lazy="raise")

    @property
    def subtotal_cents(self):
        return self.qty * self.unit_price_cents
