from sqlalchemy import Column, BigInteger, String, Enum, DateTime, ForeignKey
from app.db.session import Base

class Shipment(Base):
    __tablename__ = "shipments"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False)
    company = Column(String(64), nullable=False)
    tracking_no = Column(String(64), nullable=False)
    status = Column(Enum("CREATED","SHIPPED","DELIVERED"), default="CREATED", nullable=False)
    shipped_at = Column(DateTime)
    delivered_at = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)