from ..errors import ApiError
from ..extensions import db
from ..models import Order, OrderItem, Product


def create_order(items):
    # Consistent lock order reduces deadlocks on PostgreSQL. Conditional UPDATE
    # also protects stock on SQLite, where FOR UPDATE is ignored.
    items = sorted(items, key=lambda item: item["product_id"])
    products = db.session.scalars(
        db.select(Product)
        .where(Product.id.in_([item["product_id"] for item in items]),
               Product.archived.is_(False))
        .order_by(Product.id).with_for_update()
    ).all()
    by_id = {product.id: product for product in products}
    order = Order(items=[])
    try:
        for item in items:
            product = by_id.get(item["product_id"])
            if product is None:
                raise ApiError("not_found", f"Product {item['product_id']} not found", 404)
            result = db.session.execute(
                db.update(Product)
                .where(Product.id == product.id, Product.archived.is_(False),
                       Product.qty_in_stock >= item["qty"])
                .values(qty_in_stock=Product.qty_in_stock - item["qty"])
            )
            if result.rowcount != 1:
                raise ApiError("out_of_stock", f"Not enough stock for product {product.id}", 409)
            order.items.append(OrderItem(
                product_id=product.id, qty=item["qty"],
                unit_price_cents=product.price_cents,
            ))
        db.session.add(order)
        db.session.flush()
        order_id = order.id
        db.session.commit()
        return order_id
    except Exception:
        db.session.rollback()
        raise
