from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.models.users import User
from app.models.admins import Admin

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme_user = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme_admin = OAuth2PasswordBearer(tokenUrl="/admin/api/v1/auth/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def create_access_token(subject: str, expires_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.APP_SECRET_KEY, algorithm="HS256")

def parse_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.APP_SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")
    except JWTError:
        return None

async def get_current_user(token: str = Depends(oauth2_scheme_user), db: Session = Depends(get_db)) -> User:
    sub = parse_token(token)
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == int(sub), User.is_deleted == 0, User.status == "ACTIVE").first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or disabled")
    return user

async def get_current_admin(token: str = Depends(oauth2_scheme_admin), db: Session = Depends(get_db)) -> Admin:
    sub = parse_token(token)
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    admin = db.query(Admin).filter(Admin.id == int(sub), Admin.status == "ACTIVE").first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found or disabled")
    return admin