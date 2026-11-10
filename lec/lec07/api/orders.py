from flask import Blueprint, url_for
from sqlalchemy.orm import selectinload

from ..extensions import db
from ..models import Order, OrderItem
from ..schemas import OrderIn, OrderOut
from ..services.orders import create_order
from .common import json_body, pagination

orders_bp = Blueprint("orders", __name__, url_prefix="/api/v1/orders")


def orders_query():
    # Orders, items, products: three batched SELECTs, without per-item queries.
    return db.select(Order).options(
        selectinload(Order.items).selectinload(OrderItem.product)
    )


@orders_bp.post("")
def post_order():
    body = OrderIn().load(json_body())
    order_id = create_order(body["items"])
    order = db.session.scalars(orders_query().where(Order.id == order_id)).one()
    return OrderOut().dump(order), 201, {"Location": url_for("orders.get_order", id=order_id)}


@orders_bp.get("/<int:id>")
def get_order(id):
    order = db.first_or_404(orders_query().where(Order.id == id))
    return OrderOut().dump(order), 200


@orders_bp.get("")
def list_orders():
    page, size = pagination()
    orders = db.session.scalars(
        orders_query().order_by(Order.id).offset((page - 1) * size).limit(size)
    ).all()
    total = db.session.scalar(db.select(db.func.count()).select_from(Order))
    return {"items": OrderOut(many=True).dump(orders),
            "page": page, "size": size, "total": total}, 200
