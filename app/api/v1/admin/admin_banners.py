from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.banners import Banner
from app.schemas.admin import BannerCreate, BannerUpdate
from app.schemas.common import ok, err

router = APIRouter()

@router.get("/banners")
def list_banners(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    rows = db.query(Banner).order_by(Banner.sort_order.asc()).all()
    return ok([{"id": r.id, "image_url": r.image_url, "link_url": r.link_url, "sort_order": r.sort_order, "is_active": r.is_active} for r in rows])

@router.post("/banners")
def create_banner(req: BannerCreate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    b = Banner(image_url=req.image_url, link_url=req.link_url, sort_order=req.sort_order, is_active=req.is_active, created_at=datetime.now(), updated_at=datetime.now())
    db.add(b)
    db.commit()
    db.refresh(b)
    return ok({"id": b.id})

@router.patch("/banners/{bid}")
def update_banner(bid: int, req: BannerUpdate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    b = db.query(Banner).filter(Banner.id == bid).first()
    if not b:
        return err("Banner不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(b, k, v)
    b.updated_at = datetime.now()
    db.commit()
    return ok(True)

@router.delete("/banners/{bid}")
def delete_banner(bid: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    b = db.query(Banner).filter(Banner.id == bid).first()
    if not b:
        return err("Banner不存在")
    db.delete(b)
    db.commit()
    return ok(True)