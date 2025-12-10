from sqlalchemy import Column, BigInteger, Integer, DateTime, ForeignKey, Boolean
from app.db.session import Base

class Cart(Base):
    __tablename__ = "carts"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    cart_id = Column(BigInteger, ForeignKey("carts.id"), nullable=False)
    sku_id = Column(BigInteger, ForeignKey("product_skus.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    selected = Column(Boolean, default=True, nullable=False) # 新增此行
    created_at = Column(DateTime)
    updated_at = Column(DateTime)