from sqlalchemy import Column, BigInteger, String, Enum, DateTime, DECIMAL, Integer, ForeignKey
from app.db.session import Base

class Order(Base):
    __tablename__ = "orders"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_no = Column(String(64), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    receiver_name = Column(String(64), nullable=False)
    receiver_phone = Column(String(20), nullable=False)
    province = Column(String(64), nullable=False)
    city = Column(String(64), nullable=False)
    district = Column(String(64), nullable=False)
    address_detail = Column(String(255), nullable=False)
    remark = Column(String(255))
    status = Column(Enum("UNPAID","PAID","SHIPPING","SHIPPED","COMPLETED","CANCELED"), default="UNPAID", nullable=False)
    amount_total = Column(DECIMAL(10,2), nullable=False)
    amount_payable = Column(DECIMAL(10,2), nullable=False)
    pay_channel = Column(Enum("NONE","ALIPAY"), default="NONE", nullable=False)
    paid_at = Column(DateTime)
    canceled_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False)
    product_id = Column(BigInteger, ForeignKey("products.id"))
    sku_id = Column(BigInteger, ForeignKey("product_skus.id"))
    title = Column(String(255), nullable=False)
    sku_attrs = Column(String(1024))  # 保存 JSON 字符串
    unit_price = Column(DECIMAL(10,2), nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(DECIMAL(10,2), nullable=False)
    cover_image = Column(String(512))
    created_at = Column(DateTime)