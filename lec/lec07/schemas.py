from marshmallow import Schema, fields, validate

# ─── output ───
class ProductOut(Schema):
    id = fields.Int()
    sku = fields.Str()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    price = fields.Float()
    qty_in_stock = fields.Int()
    archived = fields.Bool()


# ─── input tạo mới ───
class ProductIn(Schema):
    sku = fields.Str(required=True,
        validate=validate.Length(min=3, max=32))
    
    name = fields.Str(required=True,
        validate=validate.Length(min=1, max=255))

    description = fields.Str(allow_none=True,
        validate=validate.Length(max=2000))
    price = fields.Float(required=True,
        validate=validate.Range(min=0))
    
    qty_in_stock = fields.Int(load_default=0, strict=True,
        validate=validate.Range(min=0))

    
class ProductPatch(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=255))
    price = fields.Float(
        validate=validate.Range(min=0))

    
# ─── /reserve ───
class ReserveIn(Schema):
    qty = fields.Int(required=True, strict=True,
        validate=validate.Range(min=1))
