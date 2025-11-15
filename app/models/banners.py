from sqlalchemy import Column, BigInteger, String, Integer, DateTime
from app.db.session import Base

class Banner(Base):
    __tablename__ = "banners"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    image_url = Column(String(512), nullable=False)
    link_url = Column(String(512))
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)