from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.categories import Category
from app.schemas.admin import CategoryCreate, CategoryUpdate
from app.schemas.common import ok, err

router = APIRouter()

@router.get("/categories")
def list_categories(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    rows = db.query(Category).order_by(Category.sort_order.asc()).all()
    return ok([{
        "id": r.id, "parent_id": r.parent_id, "name": r.name, "level": r.level, "sort_order": r.sort_order, "is_visible": r.is_visible
    } for r in rows])

@router.post("/categories")
def create_category(req: CategoryCreate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    c = Category(
        parent_id=req.parent_id,
        name=req.name,
        level=req.level,
        sort_order=req.sort_order,
        is_visible=req.is_visible,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return ok({"id": c.id})

@router.patch("/categories/{cid}")
def update_category(cid: int, req: CategoryUpdate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    c = db.query(Category).filter(Category.id == cid).first()
    if not c:
        return err("分类不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    c.updated_at = datetime.now()
    db.commit()
    return ok(True)

@router.delete("/categories/{cid}")
def delete_category(cid: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    c = db.query(Category).filter(Category.id == cid).first()
    if not c:
        return err("分类不存在")
    db.delete(c)
    db.commit()
    return ok(True)