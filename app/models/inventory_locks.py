from sqlalchemy import Column, BigInteger, Integer, Enum, DateTime, ForeignKey
from app.db.session import Base

class InventoryLock(Base):
    __tablename__ = "inventory_locks"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False)
    sku_id = Column(BigInteger, ForeignKey("product_skus.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(Enum("LOCKED","RELEASED","CONSUMED"), default="LOCKED", nullable=False)
    expires_at = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)