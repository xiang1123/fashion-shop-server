from typing import Any, Optional, List
from pydantic import BaseModel

class Resp(BaseModel):
    code: int = 0
    message: str = "ok"
    data: Optional[Any] = None

# 【关键】定义分页返回结构
class PageResult(BaseModel):
    total: int
    list: List[Any]
    page: int
    page_size: int

def ok(data: Any = None) -> dict:
    return {"code": 0, "message": "ok", "data": data}

def err(message: str, code: int = 1, data: Any = None) -> dict:
    return {"code": code, "message": message, "data": data}