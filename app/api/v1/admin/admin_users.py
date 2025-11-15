from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.users import User
from app.schemas.common import ok, err

router = APIRouter()

@router.get("/users")
def list_users(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    q = db.query(User)
    total = q.count()
    rows = q.order_by(User.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    return ok({"total": total, "list": [{"id": u.id, "email": u.email, "phone": u.phone, "nickname": u.nickname, "status": u.status} for u in rows]})

@router.get("/users/{uid}")
def user_detail(uid: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    u = db.query(User).filter(User.id == uid).first()
    if not u:
        return err("用户不存在")
    return ok({"id": u.id, "email": u.email, "phone": u.phone, "nickname": u.nickname, "status": u.status})