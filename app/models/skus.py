from sqlalchemy import Column, BigInteger, String, Integer, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from app.db.session import Base


class ProductSKU(Base):
    __tablename__ = "product_skus"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey("products.id"), nullable=False)
    sku_code = Column(String(64), unique=True, nullable=False)
    color = Column(String(64))
    size = Column(String(64))

    # 修正：使用 DECIMAL (大写)
    price = Column(DECIMAL(10, 2), nullable=False)

    stock = Column(Integer, default=0, nullable=False)
    image = Column(String(512))
    bar_code = Column(String(64))

    # 状态
    is_active = Column(Integer, default=1, nullable=False)

    # 【新增】软删除标记 (0:正常, 1:已删除)
    is_deleted = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime)
    updated_at = Column(DateTime)