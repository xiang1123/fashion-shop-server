from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.auth import RegisterReq, LoginReq, TokenResp, ProfileResp
from app.schemas.common import ok, err
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.models.users import User
from datetime import datetime

router = APIRouter()

@router.post("/auth/register")
def register(req: RegisterReq, db: Session = Depends(get_db)):
    if not req.email and not req.phone:
        return err("邮箱或手机号必须提供")
    if req.email:
        exist = db.query(User).filter(User.email == req.email).first()
        if exist:
            return err("邮箱已注册")
    if req.phone:
        exist = db.query(User).filter(User.phone == req.phone).first()
        if exist:
            return err("手机号已注册")

    user = User(
        email=req.email,
        phone=req.phone,
        password_hash=hash_password(req.password),
        nickname=req.nickname,
        status="ACTIVE",
        is_deleted=0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id))
    return ok({"token": token, "expires_in": 60*60*24*30})

@router.post("/auth/login")
def login(req: LoginReq, db: Session = Depends(get_db)):
    user = None
    if req.email:
        user = db.query(User).filter(User.email == req.email).first()
    elif req.phone:
        user = db.query(User).filter(User.phone == req.phone).first()
    else:
        return err("邮箱或手机号必须提供")

    if not user or not verify_password(req.password, user.password_hash):
        return err("账号或密码错误")
    if user.status != "ACTIVE":
        return err("账号已禁用")

    user.last_login_at = datetime.now()
    db.commit()
    token = create_access_token(str(user.id))
    return ok({"token": token, "expires_in": 60*60*24*30})

@router.get("/auth/profile")
def profile(user: User = Depends(get_current_user)):
    data = ProfileResp(
        id=user.id,
        email=user.email,
        phone=user.phone,
        nickname=user.nickname,
        avatar=user.avatar,
    )
    return ok(data.model_dump())

@router.patch("/auth/profile")
def update_profile(payload: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    nickname = payload.get("nickname")
    avatar = payload.get("avatar")
    if nickname is not None:
        user.nickname = nickname
    if avatar is not None:
        user.avatar = avatar
    user.updated_at = datetime.now()
    db.commit()
    return ok(True)