from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.skus import ProductSKU
from app.schemas.common import ok, err

router = APIRouter()

@router.get("/skus/{sid}/stock")
def get_stock(sid: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    s = db.query(ProductSKU).filter(ProductSKU.id == sid).first()
    if not s:
        return err("SKU不存在")
    return ok({"stock": s.stock})

@router.patch("/skus/{sid}/stock")
def patch_stock(sid: int, payload: dict, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    s = db.query(ProductSKU).filter(ProductSKU.id == sid).first()
    if not s:
        return err("SKU不存在")
    stock = payload.get("stock")
    if stock is None or stock < 0:
        return err("库存非法")
    s.stock = stock
    db.commit()
    return ok(True)