from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.products import Product
from app.models.skus import ProductSKU
from app.schemas.admin import ProductCreate, ProductUpdate, SKUCreate, SKUUpdate
from app.schemas.common import ok, err

router = APIRouter()

@router.get("/products")
def list_products(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    rows = db.query(Product).order_by(Product.id.desc()).all()
    return ok([{
        "id": r.id, "title": r.title, "subtitle": r.subtitle, "status": r.status, "category_id": r.category_id, "cover_image": r.cover_image
    } for r in rows])

@router.post("/products")
def create_product(req: ProductCreate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    p = Product(
        category_id=req.category_id,
        title=req.title,
        subtitle=req.subtitle,
        description=req.description,
        cover_image=req.cover_image,
        status=req.status,
        is_deleted=0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return ok({"id": p.id})

@router.patch("/products/{pid}")
def update_product(pid: int, req: ProductUpdate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    p = db.query(Product).filter(Product.id == pid).first()
    if not p:
        return err("商品不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    p.updated_at = datetime.now()
    db.commit()
    return ok(True)

@router.delete("/products/{pid}")
def delete_product(pid: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    p = db.query(Product).filter(Product.id == pid).first()
    if not p:
        return err("商品不存在")
    db.delete(p)  # 物理删除
    db.commit()
    return ok(True)

@router.get("/products/{pid}/skus")
def list_skus(pid: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    rows = db.query(ProductSKU).filter(ProductSKU.product_id == pid).all()
    return ok([{
        "id": r.id, "sku_code": r.sku_code, "color": r.color, "size": r.size, "price": float(r.price), "stock": r.stock, "image": r.image, "is_active": r.is_active
    } for r in rows])

@router.post("/products/{pid}/skus")
def create_sku(pid: int, req: SKUCreate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    if req.product_id != pid:
        return err("路径与请求不一致")
    s = ProductSKU(
        product_id=pid,
        sku_code=req.sku_code,
        color=req.color,
        size=req.size,
        price=req.price,
        stock=req.stock,
        image=req.image,
        bar_code=req.bar_code,
        is_active=req.is_active,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return ok({"id": s.id})

@router.patch("/skus/{sid}")
def update_sku(sid: int, req: SKUUpdate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    s = db.query(ProductSKU).filter(ProductSKU.id == sid).first()
    if not s:
        return err("SKU不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    s.updated_at = datetime.now()
    db.commit()
    return ok(True)

@router.delete("/skus/{sid}")
def delete_sku(sid: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    s = db.query(ProductSKU).filter(ProductSKU.id == sid).first()
    if not s:
        return err("SKU不存在")
    s.is_active = 0
    s.updated_at = datetime.now()
    db.commit()
    return ok(True)