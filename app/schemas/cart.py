from pydantic import BaseModel
from typing import List

class CartItemCreate(BaseModel):
    sku_id: int
    quantity: int

class CartItemUpdate(BaseModel):
    quantity: int

class CartItemResp(BaseModel):
    id: int
    sku_id: int
    title: str
    image: str
    unit_price: float
    quantity: int
    total_price: float

class CartResp(BaseModel):
    items: List[CartItemResp]
    amount_total: float