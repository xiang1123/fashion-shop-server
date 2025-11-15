from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.orders import Order
from app.schemas.common import ok

router = APIRouter()

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    total_orders = db.query(Order).count()
    paid_orders = db.query(Order).filter(Order.status == "PAID").count()
    unshipped = db.query(Order).filter(Order.status == "PAID").count()
    return ok({"total_orders": total_orders, "paid_orders": paid_orders, "unshipped": unshipped})