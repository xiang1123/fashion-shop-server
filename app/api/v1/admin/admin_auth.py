from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.session import get_db
from app.schemas.admin import AdminLoginReq
from app.schemas.common import ok, err
from app.core.security import verify_password, create_access_token, get_current_admin
from app.models.admins import Admin

router = APIRouter()

@router.post("/auth/login")
def admin_login(req: AdminLoginReq, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == req.username).first()
    if not admin or not verify_password(req.password, admin.password_hash):
        return err("账号或密码错误")
    if admin.status != "ACTIVE":
        return err("管理员已禁用")
    admin.last_login_at = datetime.now()
    db.commit()
    token = create_access_token(str(admin.id))
    return ok({"token": token, "expires_in": 60*60*24*30})