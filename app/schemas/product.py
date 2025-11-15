from pydantic import BaseModel
from typing import Optional, List

class BannerResp(BaseModel):
    id: int
    image_url: str
    link_url: Optional[str] = None
    sort_order: int

class CategoryResp(BaseModel):
    id: int
    parent_id: Optional[int] = None
    name: str
    level: int
    sort_order: int
    is_visible: int

class ProductResp(BaseModel):
    id: int
    title: str
    subtitle: Optional[str] = None
    cover_image: Optional[str] = None
    status: str
    category_id: Optional[int] = None

class SKUResp(BaseModel):
    id: int
    sku_code: str
    color: Optional[str] = None
    size: Optional[str] = None
    price: float
    stock: int
    image: Optional[str] = None