from pydantic import BaseModel
from typing import Optional

class AddressCreate(BaseModel):
    contact_name: str
    contact_phone: str
    province: str
    city: str
    district: str
    detail: str
    is_default: bool = False

class AddressUpdate(BaseModel):
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    detail: Optional[str] = None
    is_default: Optional[bool] = None