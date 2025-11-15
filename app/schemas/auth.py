from pydantic import BaseModel, EmailStr
from typing import Optional

class RegisterReq(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str
    nickname: Optional[str] = None

class LoginReq(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str

class TokenResp(BaseModel):
    token: str
    expires_in: int

class ProfileResp(BaseModel):
    id: int
    email: Optional[str] = None
    phone: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None