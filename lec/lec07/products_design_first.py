from pathlib import Path

import yaml
from flask import Flask, request
from flask.views import MethodView
from jsonschema import Draft202012Validator, ValidationError

app = Flask(__name__)

# BƯỚC 2: Dùng schema đã thiết kế, không khai báo lại model bằng Python.
spec = yaml.safe_load(
    Path(__file__).with_name("products_openapi.yaml").read_text(encoding="utf-8")
)
product_schema = spec["components"]["schemas"]["Product"]
Draft202012Validator.check_schema(product_schema)
validator = Draft202012Validator(product_schema)
products = []  # Lưu trong RAM; dữ liệu mất khi khởi động lại.


# BƯỚC 3: Hiện thực đúng đường dẫn, phương thức và mã phản hồi trong hợp đồng.
class ProductsAPI(MethodView):
    def get(self):
        return products, 200

    def post(self):
        product = request.get_json()
        try:
            validator.validate(product)
        except ValidationError as error:
            return {"error": error.message}, 422
        products.append(product)
        return product, 201


app.add_url_rule("/products", view_func=ProductsAPI.as_view("products"))


@app.get("/openapi.json")
def get_spec():
    """Trả hợp đồng đã viết trong YAML, không suy ra đặc tả từ code."""
    return spec


if __name__ == "__main__":
    app.run(port=5001, debug=True)
