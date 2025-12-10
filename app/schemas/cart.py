from pydantic import BaseModel
from typing import List, Optional  # 引入 Optional

class CartItemCreate(BaseModel):
    sku_id: int
    quantity: int

class CartItemUpdate(BaseModel):
    # 将 quantity 改为可选，并添加 selected
    quantity: Optional[int] = None
    selected: Optional[bool] = None

class CartItemResp(BaseModel):
    id: int
    sku_id: int
    title: str
    image: str
    unit_price: float
    quantity: int
    total_price: float
    selected: bool = True # 响应中增加 selected 字段

class CartResp(BaseModel):
    items: List[CartItemResp]
    amount_total: float