from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Products API - Code-first")

class Product(BaseModel):
    name: str = Field(min_length=1, examples=["Bút bi"])
    price: float = Field(gt=0, examples=[5000])

products: list[Product] = []

@app.post("/products", status_code=201)
def create_product(product: Product) -> Product:
    """Thêm sản phẩm. Dữ liệu sai (ví dụ giá <= 0) tự động trả lỗi 422."""
    products.append(product)
    return product


@app.get("/products")
def list_products() -> list[Product]:
    """Lấy danh sách sản phẩm đã thêm."""
    return products
