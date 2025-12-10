from datetime import datetime
import random
from sqlalchemy.orm import Session

# 导入模型
from app.models.orders import Order, OrderItem
from app.models.skus import ProductSKU
from app.models.products import Product

try:
    from app.models.addresses import Address
except ImportError:
    from app.models.address import Address

try:
    from app.models.carts import Cart, CartItem
except ImportError:
    from app.models.cart import Cart

    CartItem = None


def generate_order_no():
    """生成唯一订单号"""
    return datetime.now().strftime('%Y%m%d%H%M%S') + str(random.randint(1000, 9999))


def create_order_from_cart(db: Session, user_id: int, address_id: int, remark: str = None):
    # 1. 查询收货地址
    addr = db.query(Address).filter(Address.id == address_id).first()
    if not addr:
        raise ValueError("收货地址不存在")

    # 2. 查询用户购物车
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        raise ValueError("购物车为空")

    # 查询购物车内的商品项
    cart_items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
    if not cart_items:
        raise ValueError("购物车为空，无法提交订单")

    # 3. 准备订单数据
    order_no = generate_order_no()
    total_amount = 0
    items_to_add = []

    # 4. 创建订单对象
    new_order = Order(
        order_no=order_no,
        user_id=user_id,
        status="UNPAID",
        receiver_name=addr.contact_name,
        receiver_phone=addr.contact_phone,

        # 填充地址字段
        province=addr.province,
        city=addr.city,
        district=addr.district,
        address_detail=addr.detail,

        amount_total=0,
        amount_payable=0,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    # 5. 处理商品项 & 扣库存
    for item in cart_items:
        # item 是 CartItem 对象，有 sku_id, quantity
        sku = db.query(ProductSKU).filter(ProductSKU.id == item.sku_id).first()
        if not sku:
            continue

        # 获取关联商品信息 (用于快照)
        product = db.query(Product).filter(Product.id == sku.product_id).first()
        if not product:
            continue

        if sku.stock < item.quantity:
            raise ValueError(f"商品SKU({sku.sku_code})库存不足")

        # 扣库存
        sku.stock -= item.quantity

        # 计算金额
        line_total = sku.price * item.quantity
        total_amount += line_total

        # 构造 SKU 属性
        sku_attrs_data = {
            "color": sku.color,
            "size": sku.size,
            "sku_code": sku.sku_code
        }

        # 确定图片 (优先 SKU 图片)
        final_image = sku.image if sku.image else product.cover_image

        # 创建订单项
        order_item = OrderItem(
            product_id=sku.product_id,
            sku_id=sku.id,
            title=product.title,  # 快照标题
            sku_attrs=sku_attrs_data,  # 快照属性
            unit_price=sku.price,  # 快照单价
            quantity=item.quantity,
            total_price=line_total,  # 快照总价
            cover_image=final_image  # 快照图片
        )
        items_to_add.append(order_item)

    if not items_to_add:
        raise ValueError("有效商品为空，无法下单")

    # 6. 更新总金额
    new_order.amount_total = total_amount
    new_order.amount_payable = total_amount

    # 7. 提交事务
    try:
        db.add(new_order)
        db.flush()  # 获取 order_id

        for order_item in items_to_add:
            order_item.order_id = new_order.id
            db.add(order_item)

        # 【清理购物车】只删除 CartItem
        for item in cart_items:
            db.delete(item)

        db.commit()
        db.refresh(new_order)
        return new_order

    except Exception as e:
        db.rollback()
        raise e


def cancel_order(db: Session, order_id: int, user_id: int = None):
    """取消订单并返还库存"""
    query = db.query(Order).filter(Order.id == order_id)
    if user_id:
        query = query.filter(Order.user_id == user_id)

    order = query.first()
    if not order:
        raise ValueError("订单不存在")

    if order.status not in ['UNPAID', 'PENDING']:
        raise ValueError("当前状态无法取消")

    # 返还库存
    for item in order.items:
        if item.sku_id:
            sku = db.query(ProductSKU).filter(ProductSKU.id == item.sku_id).first()
            if sku:
                sku.stock += item.quantity

    order.status = 'CANCELLED'
    order.updated_at = datetime.now()
    db.commit()
    return order


def consume_inventory_on_paid(db: Session, order_no: str):
    pass


def get_or_create_cart(db: Session, user_id: int):
    """获取或创建购物车对象"""
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id, created_at=datetime.now(), updated_at=datetime.now())
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart