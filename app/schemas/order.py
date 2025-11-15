from pydantic import BaseModel
from typing import Optional, List

class CreateOrderReq(BaseModel):
    address_id: int
    remark: Optional[str] = None

class OrderItemResp(BaseModel):
    sku_id: Optional[int] = None
    title: str
    sku_attrs: Optional[str] = None
    unit_price: float
    quantity: int
    total_price: float
    cover_image: Optional[str] = None

class OrderResp(BaseModel):
    id: int
    order_no: str
    status: str
    amount_total: float
    amount_payable: float
    receiver_name: str
    receiver_phone: str
    address: str
    items: List[OrderItemResp]