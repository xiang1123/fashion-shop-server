from sqlalchemy import Column, BigInteger, String, Enum, DateTime
from app.db.session import Base

class Admin(Base):
    __tablename__ = "admins"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(64), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("SUPER", "OPERATOR"), default="OPERATOR", nullable=False)
    status = Column(Enum("ACTIVE", "DISABLED"), default="ACTIVE", nullable=False)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)