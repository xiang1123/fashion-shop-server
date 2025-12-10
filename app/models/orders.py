from sqlalchemy import Column, BigInteger, String, DECIMAL, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_no = Column(String(64), unique=True, nullable=False)
    user_id = Column(BigInteger, nullable=False)

    amount_total = Column(DECIMAL(10, 2), default=0)
    amount_payable = Column(DECIMAL(10, 2), default=0)

    status = Column(String(32), default="PENDING")

    receiver_name = Column(String(64))
    receiver_phone = Column(String(32))

    # 地址相关字段
    province = Column(String(64), nullable=False)
    city = Column(String(64), nullable=False)
    district = Column(String(64), nullable=False)
    address_detail = Column(String(255), nullable=False)

    ship_company = Column(String(64))
    ship_no = Column(String(64))
    ship_time = Column(DateTime)

    pay_time = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    # 【新增】订单备注字段
    remark = Column(String(255))

    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"))
    product_id = Column(BigInteger, ForeignKey("products.id"))
    sku_id = Column(BigInteger, ForeignKey("product_skus.id"))

    # 订单项详情
    title = Column(String(255), nullable=False)
    sku_attrs = Column(JSON)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    quantity = Column(Integer, default=1)
    total_price = Column(DECIMAL(10, 2), nullable=False)
    cover_image = Column(String(512))

    order = relationship("Order", back_populates="items")
    product = relationship("app.models.products.Product")
    sku = relationship("app.models.skus.ProductSKU")