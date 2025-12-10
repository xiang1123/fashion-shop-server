from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.users import User
from app.models.orders import Order
from app.models.shipments import Shipment
from app.schemas.common import ok, err

router = APIRouter()


@router.get("/orders/{oid}/shipment")
def get_shipment(oid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == oid, Order.user_id == user.id).first()
    if not order:
        return err("订单不存在")

    # 优先从 Order 表读取物流信息
    if order.ship_company and order.ship_no:
        return ok({
            "company": order.ship_company,
            "tracking_no": order.ship_no,
            "status": order.status,
            "shipped_at": order.ship_time,
            "delivered_at": None,
        })

    # 否则查询 Shipment 表
    ship = db.query(Shipment).filter(Shipment.order_id == order.id).first()
    if not ship:
        return ok(None)

    return ok({
        "company": ship.company,
        "tracking_no": ship.tracking_no,
        "status": ship.status,
        "shipped_at": ship.shipped_at,
        "delivered_at": ship.delivered_at,
    })