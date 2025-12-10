from sqlalchemy import Column, BigInteger, String, DECIMAL, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


# 尽量避免循环导入，使用字符串形式的 relationship
# 假设 Product 在 app.models.products, ProductSKU 在 app.models.skus

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
    address = Column(String(255))

    ship_company = Column(String(64))
    ship_no = Column(String(64))
    ship_time = Column(DateTime)

    pay_time = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"))
    product_id = Column(BigInteger, ForeignKey("products.id"))
    sku_id = Column(BigInteger, ForeignKey("product_skus.id"))

    price = Column(DECIMAL(10, 2))
    quantity = Column(Integer, default=1)

    order = relationship("Order", back_populates="items")
    # 关键：添加这两个关联
    product = relationship("app.models.products.Product")
    sku = relationship("app.models.skus.ProductSKU")