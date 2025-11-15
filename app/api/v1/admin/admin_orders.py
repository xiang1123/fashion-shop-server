from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.orders import Order, OrderItem
from app.models.shipments import Shipment
from app.schemas.admin import ShipReq
from app.schemas.common import ok, err

router = APIRouter()

@router.get("/orders")
def list_orders(status: str | None = None, page: int = 1, page_size: int = 20, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    total = q.count()
    rows = q.order_by(Order.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    data = []
    for o in rows:
        items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
        data.append({
            "id": o.id, "order_no": o.order_no, "status": o.status, "amount_payable": float(o.amount_payable),
            "user_id": o.user_id, "created_at": o.created_at,
            "items": [{"title": it.title, "quantity": it.quantity, "unit_price": float(it.unit_price)} for it in items]
        })
    return ok({"total": total, "list": data})

@router.get("/orders/{oid}")
def order_detail(oid: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    o = db.query(Order).filter(Order.id == oid).first()
    if not o:
        return err("订单不存在")
    items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
    return ok({
        "id": o.id, "order_no": o.order_no, "status": o.status, "amount_total": float(o.amount_total),
        "amount_payable": float(o.amount_payable), "receiver_name": o.receiver_name,
        "address": f"{o.province}{o.city}{o.district}{o.address_detail}",
        "items": [{"title": it.title, "quantity": it.quantity, "unit_price": float(it.unit_price), "total_price": float(it.total_price)} for it in items]
    })

@router.post("/orders/{oid}/ship")
def ship(oid: int, req: ShipReq, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    o = db.query(Order).filter(Order.id == oid).first()
    if not o:
        return err("订单不存在")
    if o.status not in ("PAID", "SHIPPING"):
        return err("订单未支付或状态不允许发货")
    ship = db.query(Shipment).filter(Shipment.order_id == o.id).first()
    if not ship:
        ship = Shipment(order_id=o.id, company=req.company, tracking_no=req.tracking_no, status="SHIPPED", shipped_at=datetime.now(), created_at=datetime.now(), updated_at=datetime.now())
        db.add(ship)
    else:
        ship.company = req.company
        ship.tracking_no = req.tracking_no
        ship.status = "SHIPPED"
        ship.shipped_at = datetime.now()
        ship.updated_at = datetime.now()
    o.status = "SHIPPING"
    o.updated_at = datetime.now()
    db.commit()
    return ok(True)

@router.post("/orders/{oid}/cancel")
def cancel(oid: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    o = db.query(Order).filter(Order.id == oid).first()
    if not o:
        return err("订单不存在")
    o.status = "CANCELED"
    o.canceled_at = datetime.now()
    o.updated_at = datetime.now()
    db.commit()
    return ok(True)