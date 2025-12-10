from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.users import User
from app.models.carts import Cart, CartItem
from app.models.skus import ProductSKU
from app.models.products import Product
from app.services.order import get_or_create_cart
from app.schemas.cart import CartItemCreate, CartItemUpdate
from app.schemas.common import ok, err

router = APIRouter()


@router.get("/cart")
def get_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cart = get_or_create_cart(db, user.id)
    items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
    resp_items = []
    amount_total = 0.0
    for it in items:
        sku = db.query(ProductSKU).filter(ProductSKU.id == it.sku_id).first()
        product = db.query(Product).filter(Product.id == sku.product_id).first() if sku else None
        unit_price = float(sku.price) if sku else 0.0
        total_price = round(unit_price * it.quantity, 2)

        # 【修改】只计算选中商品的总价
        if it.selected:
            amount_total += total_price

        resp_items.append({
            "id": it.id,
            "sku_id": it.sku_id,
            "title": product.title if product else f"SKU-{it.sku_id}",
            "image": sku.image if sku else "",
            "unit_price": unit_price,
            "quantity": it.quantity,
            "total_price": total_price,
            "selected": it.selected  # 【新增】返回选中状态
        })
    return ok({"items": resp_items, "amount_total": round(amount_total, 2)})


@router.post("/cart/items")
def add_item(req: CartItemCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cart = get_or_create_cart(db, user.id)
    sku = db.query(ProductSKU).filter(ProductSKU.id == req.sku_id, ProductSKU.is_active == 1).first()
    if not sku:
        return err("SKU不存在或不可用")
    item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.sku_id == req.sku_id).first()
    if item:
        item.quantity += req.quantity
        item.selected = True  # 添加时默认选中
        item.updated_at = datetime.now()
    else:
        item = CartItem(cart_id=cart.id, sku_id=req.sku_id, quantity=req.quantity, selected=True,
                        created_at=datetime.now(), updated_at=datetime.now())
        db.add(item)
    db.commit()
    return ok(True)


@router.patch("/cart/items/{item_id}")
def update_item(item_id: int, req: CartItemUpdate, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    cart = get_or_create_cart(db, user.id)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        return err("购物车项不存在")

    # 【修改】分别处理数量和选中状态
    if req.quantity is not None:
        if req.quantity <= 0:
            db.delete(item)
            db.commit()
            return ok(True)
        else:
            item.quantity = req.quantity

    if req.selected is not None:
        item.selected = req.selected

    item.updated_at = datetime.now()
    db.commit()
    return ok(True)


@router.delete("/cart/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cart = get_or_create_cart(db, user.id)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        return err("购物车项不存在")
    db.delete(item)
    db.commit()
    return ok(True)


@router.post("/cart/clear")
def clear_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cart = get_or_create_cart(db, user.id)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    return ok(True)