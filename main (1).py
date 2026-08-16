from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import os
from pymongo import MongoClient
from bson import ObjectId

app = FastAPI(title="Solemate Backend API", version="1.0.0")

uri = os.getenv("MONGODB_URI")
db_name = os.getenv("MONGODB_DB", "solemate")
client = MongoClient(uri) if uri else None
db = client[db_name] if client else None

class Product(BaseModel):
    name: str
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    size: Optional[str] = None
    color: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None

class OrderItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)

class Order(BaseModel):
    customer_name: str
    phone: str
    address: str
    items: list[OrderItem]

@app.get("/")
def root():
    return {"message": "Solemate Backend is running"}

@app.get("/health")
def health():
    if not client:
        return {"status": "ok", "mongodb": "not_configured"}
    try:
        client.admin.command("ping")
        return {"status": "ok", "mongodb": "connected"}
    except Exception:
        return {"status": "ok", "mongodb": "error"}

@app.get("/products")
def get_products():
    if db is None:
        raise HTTPException(500, "MONGODB_URI is not configured")
    data = []
    for item in db.products.find().sort("_id", -1):
        item["id"] = str(item.pop("_id"))
        data.append(item)
    return data

@app.post("/products")
def add_product(product: Product):
    if db is None:
        raise HTTPException(500, "MONGODB_URI is not configured")
    doc = product.model_dump()
    result = db.products.insert_one(doc)
    return {"id": str(result.inserted_id), **doc}

@app.get("/products/{product_id}")
def get_product(product_id: str):
    if db is None:
        raise HTTPException(500, "MONGODB_URI is not configured")
    try:
        item = db.products.find_one({"_id": ObjectId(product_id)})
    except Exception:
        raise HTTPException(400, "Invalid product id")
    if not item:
        raise HTTPException(404, "Product not found")
    item["id"] = str(item.pop("_id"))
    return item

@app.post("/orders")
def create_order(order: Order):
    if db is None:
        raise HTTPException(500, "MONGODB_URI is not configured")
    doc = order.model_dump()
    doc["status"] = "pending"
    result = db.orders.insert_one(doc)
    return {"id": str(result.inserted_id), "status": "pending"}
