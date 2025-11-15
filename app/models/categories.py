from sqlalchemy import Column, BigInteger, String, Integer, DateTime, ForeignKey
from app.db.session import Base

class Category(Base):
    __tablename__ = "categories"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    parent_id = Column(BigInteger, ForeignKey("categories.id"))
    name = Column(String(128), nullable=False)
    level = Column(Integer, default=1, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    is_visible = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)