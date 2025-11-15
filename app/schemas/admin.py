from pydantic import BaseModel
from typing import Optional

class AdminLoginReq(BaseModel):
    username: str
    password: str

class AdminTokenResp(BaseModel):
    token: str
    expires_in: int

class CategoryCreate(BaseModel):
    parent_id: Optional[int] = None
    name: str
    level: int = 1
    sort_order: int = 0
    is_visible: int = 1

class CategoryUpdate(BaseModel):
    parent_id: Optional[int] = None
    name: Optional[str] = None
    level: Optional[int] = None
    sort_order: Optional[int] = None
    is_visible: Optional[int] = None

class ProductCreate(BaseModel):
    category_id: Optional[int] = None
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    status: str = "DRAFT"

class ProductUpdate(ProductCreate):
    pass

class SKUCreate(BaseModel):
    product_id: int
    sku_code: str
    color: Optional[str] = None
    size: Optional[str] = None
    price: float
    stock: int
    image: Optional[str] = None
    bar_code: Optional[str] = None
    is_active: int = 1

class SKUUpdate(BaseModel):
    color: Optional[str] = None
    size: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    image: Optional[str] = None
    bar_code: Optional[str] = None
    is_active: Optional[int] = None

class BannerCreate(BaseModel):
    image_url: str
    link_url: Optional[str] = None
    sort_order: int = 0
    is_active: int = 1

class BannerUpdate(BaseModel):
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[int] = None

class ShipReq(BaseModel):
    company: str
    tracking_no: str