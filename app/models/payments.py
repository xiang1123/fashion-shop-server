from sqlalchemy import Column, BigInteger, String, DECIMAL, Enum, DateTime, JSON, ForeignKey
from app.db.session import Base

class Payment(Base):
    __tablename__ = "payments"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False)
    channel = Column(Enum("ALIPAY"), nullable=False)
    out_trade_no = Column(String(64), nullable=False)
    trade_no = Column(String(128))
    amount = Column(DECIMAL(10,2), nullable=False)
    status = Column(Enum("INIT","SUCCESS","FAILED","CLOSED"), default="INIT", nullable=False)
    request_params = Column(JSON)
    notify_payload = Column(JSON)
    paid_at = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)