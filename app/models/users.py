from sqlalchemy import Column, BigInteger, String, Enum, DateTime, Integer, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255))
    phone = Column(String(20))
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(64))
    avatar = Column(String(512))
    status = Column(Enum("ACTIVE", "DISABLED"), default="ACTIVE", nullable=False)
    is_deleted = Column(Integer, default=0, nullable=False)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)