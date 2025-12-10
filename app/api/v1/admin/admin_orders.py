from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.orders import Order, OrderItem
from app.schemas.admin import ShipReq
from app.schemas.common import ok, err, PageResult

router = APIRouter()


# -----------------------------------------------------------------------------
# 订单列表
# -----------------------------------------------------------------------------
@router.get("/orders")
def list_orders(
        page: int = 1,
        page_size: int = 10,
        order_no: Optional[str] = None,
        status: Optional[str] = None,
        db: Session = Depends(get_db),
        admin=Depends(get_current_admin)
):
    query = db.query(Order)

    if order_no:
        query = query.filter(Order.order_no.like(f"%{order_no}%"))

    if status:
        query = query.filter(Order.status == status)

    query = query.order_by(desc(Order.created_at))

    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    data = []
    for order in rows:
        # 获取子项
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).limit(2).all()
        items_data = []
        for i in items:
            # 【修复】通过 relationship 获取商品信息，并加空值保护
            p_title = i.product.title if i.product else "未知商品"
            # 拼接规格信息：颜色+尺码
            if i.sku:
                sku_info = f"{i.sku.color or ''} {i.sku.size or ''}".strip()
            else:
                sku_info = "默认规格"

            items_data.append({
                "id": i.id,
                "title": p_title,
                "sku_info": sku_info,
                "quantity": i.quantity,
                "price": float(i.price)
            })

        data.append({
            "id": order.id,
            "order_no": order.order_no,
            "user_id": order.user_id,
            "amount_total": float(order.amount_total),
            "amount_payable": float(order.amount_payable),
            "status": order.status,
            "receiver_name": order.receiver_name,
            "receiver_phone": order.receiver_phone,
            "address": order.address,
            "created_at": order.created_at,
            "items": items_data
        })

    return ok(PageResult(total=total, list=data, page=page, page_size=page_size))


# -----------------------------------------------------------------------------
# 订单详情
# -----------------------------------------------------------------------------
@router.get("/orders/{oid}")
def get_order_detail(oid: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    order = db.query(Order).filter(Order.id == oid).first()
    if not order:
        return err("订单不存在")

    items = db.query(OrderItem).filter(OrderItem.order_id == oid).all()
    items_data = []
    for i in items:
        # 【修复】详情页也同样处理
        p_title = i.product.title if i.product else "未知商品"
        p_img = i.product.cover_image if i.product else ""
        if i.sku:
            sku_info = f"{i.sku.color or ''} {i.sku.size or ''}".strip()
        else:
            sku_info = "默认规格"

        items_data.append({
            "id": i.id,
            "product_id": i.product_id,
            "title": p_title,
            "product_image": p_img,
            "sku_id": i.sku_id,
            "sku_info": sku_info,
            "price": float(i.price),
            "quantity": i.quantity,
            "total_price": float(i.price * i.quantity)
        })

    data = {
        "id": order.id,
        "order_no": order.order_no,
        "user_id": order.user_id,
        "status": order.status,
        "amount_total": float(order.amount_total),
        "amount_payable": float(order.amount_payable),
        "created_at": order.created_at,
        "pay_time": order.pay_time,
        "ship_time": order.ship_time,
        "receiver_name": order.receiver_name,
        "receiver_phone": order.receiver_phone,
        "address": order.address,
        "items": items_data,
        "ship_company": order.ship_company,
        "ship_no": order.ship_no
    }
    return ok(data)


# -----------------------------------------------------------------------------
# 发货
# -----------------------------------------------------------------------------
@router.post("/orders/{oid}/ship")
def ship_order(oid: int, req: ShipReq, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    order = db.query(Order).filter(Order.id == oid).first()
    if not order:
        return err("订单不存在")

    if order.status != 'PAID':
        return err("只有'已支付'状态的订单才能发货")

    order.status = 'SHIPPING'
    order.ship_company = req.company
    order.ship_no = req.tracking_no
    order.ship_time = datetime.now()
    order.updated_at = datetime.now()

    db.commit()
    return ok("发货成功")


# -----------------------------------------------------------------------------
# 取消
# -----------------------------------------------------------------------------
@router.post("/orders/{oid}/cancel")
def cancel_order(oid: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    order = db.query(Order).filter(Order.id == oid).first()
    if not order:
        return err("订单不存在")

    if order.status not in ['PENDING', 'PAID']:
        return err("当前状态无法取消订单")

    order.status = 'CANCELLED'
    order.updated_at = datetime.now()

    db.commit()
    return ok("订单已取消")