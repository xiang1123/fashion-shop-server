from typing import Any, Optional
from pydantic import BaseModel

class Resp(BaseModel):
    code: int = 0
    message: str = "ok"
    data: Optional[Any] = None

def ok(data: Any = None) -> dict:
    return {"code": 0, "message": "ok", "data": data}

def err(message: str, code: int = 1, data: Any = None) -> dict:
    return {"code": code, "message": message, "data": data}