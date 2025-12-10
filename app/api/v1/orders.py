from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.users import User
from app.models.orders import Order, OrderItem
from app.services.order import create_order_from_cart, cancel_order, consume_inventory_on_paid
from app.schemas.order import CreateOrderReq
from app.schemas.common import ok, err
from datetime import datetime

router = APIRouter()

@router.post("/orders")
def create_order(req: CreateOrderReq, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        order = create_order_from_cart(db, user.id, req.address_id, req.remark)
        return ok({
            "order_id": order.id,
            "order_no": order.order_no,
            "amount_total": float(order.amount_total),
            "payable_amount": float(order.amount_payable),
            "status": order.status,
        })
    except ValueError as e:
        return err(str(e))

@router.get("/orders")
def list_orders(status: str | None = None, page: int = 1, page_size: int = 10, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Order).filter(Order.user_id == user.id)
    if status:
        q = q.filter(Order.status == status)
    total = q.count()
    rows = q.order_by(Order.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    data = []
    for o in rows:
        items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
        data.append({
            "id": o.id,
            "order_no": o.order_no,
            "status": o.status,
            "amount_total": float(o.amount_total),
            "amount_payable": float(o.amount_payable),
            "receiver_name": o.receiver_name,
            "receiver_phone": o.receiver_phone,
            "address": f"{o.province}{o.city}{o.district}{o.address_detail}",
            "items": [{
                "sku_id": it.sku_id,
                "title": it.title,
                "sku_attrs": it.sku_attrs,
                "unit_price": float(it.unit_price),
                "quantity": it.quantity,
                "total_price": float(it.total_price),
                "cover_image": it.cover_image
            } for it in items]
        })
    return ok({"total": total, "list": data})

@router.get("/orders/{oid}")
def order_detail(oid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    o = db.query(Order).filter(Order.id == oid, Order.user_id == user.id).first()
    if not o:
        return err("订单不存在")
    items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
    return ok({
        "id": o.id,
        "order_no": o.order_no,
        "status": o.status,
        "amount_total": float(o.amount_total),
        "amount_payable": float(o.amount_payable),
        "receiver_name": o.receiver_name,
        "receiver_phone": o.receiver_phone,
        "address": f"{o.province}{o.city}{o.district}{o.address_detail}",
        "items": [{
            "sku_id": it.sku_id,
            "title": it.title,
            "sku_attrs": it.sku_attrs,
            "unit_price": float(it.unit_price),
            "quantity": it.quantity,
            "total_price": float(it.total_price),
            "cover_image": it.cover_image
        } for it in items]
    })


@router.post("/orders/{oid}/cancel")
def cancel(oid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # 1. 这里已经查询出了 order 对象
    order = db.query(Order).filter(Order.id == oid, Order.user_id == user.id).first()

    if not order:
        return err("订单不存在")

    try:
        # 【修改前】错误写法：传入了整个对象
        # cancel_order(db, order)

        # 【修改后】正确写法：只传入 order.id
        cancel_order(db, order.id)

        return ok(True)
    except ValueError as e:
        return err(str(e))

@router.post("/orders/{oid}/confirm")
def confirm(oid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == oid, Order.user_id == user.id).first()
    if not order:
        return err("订单不存在")
    if order.status not in ("SHIPPED", "SHIPPING"):
        return err("订单未发货或状态不允许确认")
    order.status = "COMPLETED"
    order.completed_at = datetime.now()
    order.updated_at = datetime.now()
    db.commit()
    return ok(True)