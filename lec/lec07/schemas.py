from marshmallow import Schema, ValidationError, fields, validate, validates_schema


def nonblank(value):
    if not value.strip():
        raise ValidationError("Must not be blank.")


class ProductOut(Schema):
    id = fields.Int()
    sku = fields.Str()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    price_cents = fields.Int()
    qty_in_stock = fields.Int()
    archived = fields.Bool()


class ProductIn(Schema):
    sku = fields.Str(required=True, validate=[validate.Length(min=3, max=32), nonblank])
    name = fields.Str(required=True, validate=[validate.Length(min=1, max=255), nonblank])
    description = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    price_cents = fields.Int(required=True, strict=True, validate=validate.Range(min=0))
    qty_in_stock = fields.Int(load_default=0, strict=True, validate=validate.Range(min=0))


class ProductPatch(Schema):
    name = fields.Str(validate=[validate.Length(min=1, max=255), nonblank])
    description = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    price_cents = fields.Int(strict=True, validate=validate.Range(min=0))


class ReserveIn(Schema):
    qty = fields.Int(required=True, strict=True, validate=validate.Range(min=1))


class OrderItemIn(Schema):
    product_id = fields.Int(required=True, strict=True, validate=validate.Range(min=1))
    qty = fields.Int(required=True, strict=True, validate=validate.Range(min=1))


class OrderIn(Schema):
    items = fields.List(fields.Nested(OrderItemIn), required=True,
                        validate=validate.Length(min=1, max=100))

    @validates_schema
    def unique_products(self, data, **kwargs):
        ids = [item["product_id"] for item in data["items"]]
        if len(ids) != len(set(ids)):
            raise ValidationError("Each product may appear only once.", "items")


class OrderItemOut(Schema):
    id = fields.Int()
    product_id = fields.Int()
    qty = fields.Int()
    unit_price_cents = fields.Int()
    subtotal_cents = fields.Int()
    product = fields.Nested(ProductOut)


class OrderOut(Schema):
    id = fields.Int()
    created_at = fields.DateTime()
    items = fields.List(fields.Nested(OrderItemOut))
    total_cents = fields.Int()
