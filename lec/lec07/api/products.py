from flask import Blueprint
from sqlalchemy.exc import IntegrityError

from ..errors import ApiError
from ..extensions import db
from ..models import Product
from ..schemas import ProductIn, ProductOut, ProductPatch, ReserveIn
from .common import json_body, pagination

products_bp = Blueprint("products", __name__, url_prefix="/api/v1/products")


def get_active_product(id):
    return db.first_or_404(
        db.select(Product).where(Product.id == id, Product.archived.is_(False))
    )


@products_bp.get("")
def list_products():
    page, size = pagination()
    base = db.select(Product).where(Product.archived.is_(False))
    rows = db.session.scalars(
        base.order_by(Product.id).offset((page - 1) * size).limit(size)
    ).all()
    total = db.session.scalar(
        db.select(db.func.count()).select_from(Product).where(Product.archived.is_(False))
    )
    return {"items": ProductOut(many=True).dump(rows),
            "page": page, "size": size, "total": total}, 200


@products_bp.get("/<int:id>")
def get_product(id):
    return ProductOut().dump(get_active_product(id)), 200


@products_bp.post("")
def create_product():
    body = ProductIn().load(json_body())
    product = Product(**body)
    db.session.add(product)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        if db.session.scalar(db.select(Product.id).where(Product.sku == body["sku"])):
            raise ApiError("conflict", "SKU already exists", 409)
        raise
    return ProductOut().dump(product), 201


@products_bp.post("/<int:id>/reserve")
def reserve_product(id):
    body = ReserveIn().load(json_body())
    # Check and subtract atomically so concurrent requests cannot oversell.
    result = db.session.execute(
        db.update(Product)
        .where(Product.id == id, Product.archived.is_(False),
               Product.qty_in_stock >= body["qty"])
        .values(qty_in_stock=Product.qty_in_stock - body["qty"])
    )
    if result.rowcount == 0:
        db.session.rollback()
        get_active_product(id)
        raise ApiError("out_of_stock", "Not enough stock", 409)
    data = ProductOut().dump(get_active_product(id))
    db.session.commit()
    return data, 200


@products_bp.patch("/<int:id>")
def patch_product(id):
    body = ProductPatch().load(json_body())
    product = get_active_product(id)
    for key, value in body.items():
        setattr(product, key, value)
    db.session.commit()
    return ProductOut().dump(product), 200


@products_bp.delete("/<int:id>")
def delete_product(id):
    product = get_active_product(id)
    product.archived = True
    db.session.commit()
    return "", 204
