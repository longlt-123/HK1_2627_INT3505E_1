from flask import Blueprint, abort, jsonify, request
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models.product import Product
# from ..errors import Conflict
from ..schemas import (
    ProductOut, ProductIn, ProductPatch, ReserveIn)

products_bp = Blueprint(
    "products", __name__, url_prefix="/api/v1/products")


@products_bp.errorhandler(ValidationError)
def handle_validation_error(error):
    return jsonify({"errors": error.messages}), 422


def get_active_product(id):
    return db.first_or_404(
        db.select(Product).where(Product.id == id, Product.archived.is_(False))
    )


@products_bp.get("/<int:id>")
def get_product(id):
    return ProductOut().dump(get_active_product(id)), 200


@products_bp.post("/<int:id>/reserve")
def reserve_product(id):
    body = ReserveIn().load(request.get_json())
    # Check and subtract in one statement to prevent overselling.
    result = db.session.execute(
        db.update(Product)
        .where(Product.id == id, Product.archived.is_(False),
               Product.qty_in_stock >= body["qty"])
        .values(qty_in_stock=Product.qty_in_stock - body["qty"])
    )
    
    if result.rowcount == 0:
        db.session.rollback()
        get_active_product(id)
        return jsonify({"error": "Not enough stock"}), 409
    
    db.session.commit()
    return ProductOut().dump(get_active_product(id)), 200


@products_bp.get("")
def list_products():
    try:
        page = max(1, int(request.args.get("page", 1)))
        size = min(100, max(1, int(request.args.get("size", 20))))
    except ValueError:
        abort(400, description="page and size must be integers")
    base = db.select(Product).where(
        Product.archived.is_(False)
        )
    rows = db.session.execute(
        base.order_by(Product.id)
        .offset((page-1) * size).limit(size)
    ).scalars().all()

    return jsonify(
        {
        "items": [ProductOut().dump(p) for p in rows],
        "page": page, "size": size,
        "total": db.session.scalar(
            db.select(db.func.count()).select_from(Product)
            .where(Product.archived.is_(False))
            )
        }
    )

@products_bp.post("")
def create_product():
    body = ProductIn().load(request.get_json())
    p = Product(**body)
    db.session.add(p)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # raise Conflict("SKU đã tồn tại")
        return jsonify({"error": "SKU đã tồn tại"}), 409
    return ProductOut().dump(p), 201

@products_bp.patch("/<int:id>")
def patch_product(id):
    body = ProductPatch().load(
        request.json, partial=True)
    p = get_active_product(id)

    for k, v in body.items():
        setattr(p, k, v)
    db.session.commit()
    return ProductOut().dump(p), 200

@products_bp.delete("/<int:id>")
def delete_product(id):
    p = get_active_product(id)
    p.archived = True
    db.session.commit()
    return "", 204
