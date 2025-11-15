from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.carts import Cart, CartItem
from app.models.addresses import Address
from app.models.orders import Order, OrderItem
from app.models.skus import ProductSKU
from app.models.products import Product
from app.models.inventory_locks import InventoryLock

def gen_order_no(user_id: int) -> str:
    # Simple order no: yyyymmddHHMMSS + user tail. In production, use Redis/increment.
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{now}{user_id:06d}"

def get_or_create_cart(db: Session, user_id: int) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id, created_at=datetime.now(), updated_at=datetime.now())
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

def calc_cart_amount(db: Session, cart: Cart) -> float:
    items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
    total = 0.0
    for it in items:
        sku = db.query(ProductSKU).filter(ProductSKU.id == it.sku_id).first()
        if not sku:
            continue
        total += float(sku.price) * it.quantity
    return round(total, 2)

def create_order_from_cart(db: Session, user_id: int, address_id: int, remark: str | None) -> Order:
    cart = get_or_create_cart(db, user_id)
    cart_items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
    if not cart_items:
        raise ValueError("购物车为空")

    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user_id).first()
    if not address:
        raise ValueError("地址不存在")

    # Check stock & prelock
    total_amount = 0.0
    for it in cart_items:
        sku: ProductSKU | None = db.query(ProductSKU).filter(ProductSKU.id == it.sku_id, ProductSKU.is_active == 1).with_for_update().first()
        if not sku:
            raise ValueError(f"SKU不存在: {it.sku_id}")
        if sku.stock < it.quantity:
            raise ValueError(f"库存不足: SKU {sku.id}")
        total_amount += float(sku.price) * it.quantity

    order_no = gen_order_no(user_id)
    order = Order(
        order_no=order_no,
        user_id=user_id,
        receiver_name=address.contact_name,
        receiver_phone=address.contact_phone,
        province=address.province,
        city=address.city,
        district=address.district,
        address_detail=address.detail,
        remark=remark or "",
        status="UNPAID",
        amount_total=round(total_amount, 2),
        amount_payable=round(total_amount, 2),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(order)
    db.flush()

    # Insert order items and prelock inventory (reduce stock)
    for it in cart_items:
        sku = db.query(ProductSKU).filter(ProductSKU.id == it.sku_id).with_for_update().first()
        product = db.query(Product).filter(Product.id == sku.product_id).first()
        oi = OrderItem(
            order_id=order.id,
            product_id=sku.product_id,
            sku_id=sku.id,
            title=product.title if product else f"SKU-{sku.id}",
            sku_attrs=None,
            unit_price=sku.price,
            quantity=it.quantity,
            total_price=round(float(sku.price) * it.quantity, 2),
            cover_image=sku.image,
            created_at=datetime.now(),
        )
        db.add(oi)
        # prelock: reduce stock and record lock
        sku.stock = sku.stock - it.quantity
        lock = InventoryLock(
            order_id=order.id,
            sku_id=sku.id,
            quantity=it.quantity,
            status="LOCKED",
            expires_at=datetime.now() + timedelta(minutes=30),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(lock)

    # clear cart
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()

    db.commit()
    db.refresh(order)
    return order

def cancel_order(db: Session, order: Order):
    if order.status != "UNPAID":
        raise ValueError("只能取消未支付订单")
    order.status = "CANCELED"
    order.canceled_at = datetime.now()
    order.updated_at = datetime.now()

    locks = db.query(InventoryLock).filter(InventoryLock.order_id == order.id, InventoryLock.status == "LOCKED").with_for_update().all()
    for lk in locks:
        # release: add back stock
        sku = db.query(ProductSKU).filter(ProductSKU.id == lk.sku_id).with_for_update().first()
        if sku:
            sku.stock = sku.stock + lk.quantity
        lk.status = "RELEASED"
        lk.updated_at = datetime.now()
    db.commit()

def consume_inventory_on_paid(db: Session, order: Order):
    # inventory already reduced when prelock; mark locks as consumed
    locks = db.query(InventoryLock).filter(InventoryLock.order_id == order.id, InventoryLock.status == "LOCKED").with_for_update().all()
    for lk in locks:
        lk.status = "CONSUMED"
        lk.updated_at = datetime.now()
    db.commit()