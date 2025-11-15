from sqlalchemy import Column, BigInteger, String, Text, Enum, DateTime, ForeignKey, Integer
from app.db.session import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    category_id = Column(BigInteger, ForeignKey("categories.id"))
    title = Column(String(255), nullable=False)
    subtitle = Column(String(255))
    description = Column(Text)
    cover_image = Column(String(512))
    status = Column(Enum("DRAFT", "ON_SALE", "OFF_SALE"), default="DRAFT", nullable=False)
    is_deleted = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)