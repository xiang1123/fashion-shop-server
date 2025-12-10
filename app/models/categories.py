from sqlalchemy import Column, BigInteger, String, Integer, DateTime, ForeignKey
from app.db.session import Base


class Category(Base):
    __tablename__ = "categories"

    # id 保持原样，作为技术主键，自动递增 (63, 64, 65...)
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 新增业务编码字段，用于存储你想要的 "1", "11", "112"
    code = Column(String(64), unique=True, nullable=False, default="")

    parent_id = Column(BigInteger, ForeignKey("categories.id"))
    name = Column(String(128), nullable=False)
    level = Column(Integer, default=1, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    is_visible = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)