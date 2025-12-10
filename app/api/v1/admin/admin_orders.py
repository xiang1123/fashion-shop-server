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
            # 【修复】优先使用订单项快照中的标题，如果没有再查关联商品
            # 新版 OrderItem 模型已有 title 字段
            p_title = getattr(i, 'title', None)
            if not p_title:
                p_title = i.product.title if i.product else "未知商品"

            # 拼接规格信息：颜色+尺码
            # 新版 OrderItem 模型已有 sku_attrs 字段(JSON)，优先使用
            sku_info = "默认规格"
            if hasattr(i, 'sku_attrs') and i.sku_attrs:
                # 如果是字典类型
                if isinstance(i.sku_attrs, dict):
                    attrs = [v for k, v in i.sku_attrs.items() if v]
                    sku_info = " ".join(attrs)
            elif i.sku:
                sku_info = f"{i.sku.color or ''} {i.sku.size or ''}".strip()

            items_data.append({
                "id": i.id,
                "title": p_title,
                "sku_info": sku_info,
                "quantity": i.quantity,
                # 【修复】使用 unit_price
                "price": float(i.unit_price)
            })

        # 【修复】地址拼接
        # 如果您在 Order 模型里加了 @property address，可以直接用 order.address
        # 这里为了保险，手动拼接
        full_address = f"{order.province} {order.city} {order.district} {order.address_detail}"

        data.append({
            "id": order.id,
            "order_no": order.order_no,
            "user_id": order.user_id,
            "amount_total": float(order.amount_total),
            "amount_payable": float(order.amount_payable),
            "status": order.status,
            "receiver_name": order.receiver_name,
            "receiver_phone": order.receiver_phone,
            "address": full_address,
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
        # 【修复】优先快照信息
        p_title = getattr(i, 'title', None)
        if not p_title:
            p_title = i.product.title if i.product else "未知商品"

        p_img = getattr(i, 'cover_image', None)
        if not p_img:
            p_img = i.product.cover_image if i.product else ""

        # 规格信息
        sku_info = "默认规格"
        if hasattr(i, 'sku_attrs') and i.sku_attrs:
            if isinstance(i.sku_attrs, dict):
                attrs = [v for k, v in i.sku_attrs.items() if v]
                sku_info = " ".join(attrs)
        elif i.sku:
            sku_info = f"{i.sku.color or ''} {i.sku.size or ''}".strip()

        items_data.append({
            "id": i.id,
            "product_id": i.product_id,
            "title": p_title,
            "product_image": p_img,
            "sku_id": i.sku_id,
            "sku_info": sku_info,
            # 【修复】字段名修正
            "price": float(i.unit_price),
            "quantity": i.quantity,
            "total_price": float(i.total_price)
        })

    # 【修复】地址拼接
    full_address = f"{order.province} {order.city} {order.district} {order.address_detail}"

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
        "address": full_address,
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

    order.status = 'CANCELED'
    order.updated_at = datetime.now()

    db.commit()
    return ok("订单已取消")