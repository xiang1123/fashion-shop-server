from sqlalchemy import Column, BigInteger, String, Integer, DateTime, ForeignKey
from app.db.session import Base

class Address(Base):
    __tablename__ = "addresses"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    contact_name = Column(String(64), nullable=False)
    contact_phone = Column(String(20), nullable=False)
    province = Column(String(64), nullable=False)
    city = Column(String(64), nullable=False)
    district = Column(String(64), nullable=False)
    detail = Column(String(255), nullable=False)
    is_default = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)