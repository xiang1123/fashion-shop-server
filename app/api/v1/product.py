from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.banners import Banner
from app.models.categories import Category
from app.models.products import Product
from app.models.skus import ProductSKU
from app.schemas.common import ok

router = APIRouter()

@router.get("/banners")
def banners(db: Session = Depends(get_db)):
    rows = db.query(Banner).filter(Banner.is_active == 1).order_by(Banner.sort_order.asc()).all()
    return ok([{
        "id": r.id, "image_url": r.image_url, "link_url": r.link_url, "sort_order": r.sort_order
    } for r in rows])

@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    rows = db.query(Category).filter(Category.is_visible == 1).order_by(Category.sort_order.asc()).all()
    return ok([{
        "id": r.id, "parent_id": r.parent_id, "name": r.name, "level": r.level, "sort_order": r.sort_order, "is_visible": r.is_visible
    } for r in rows])

@router.get("/products")
def list_products(
    db: Session = Depends(get_db),
    category_id: int | None = Query(None),
    keyword: str | None = Query(None),
    page: int = 1,
    page_size: int = 10,
    sort: str | None = Query(None),
):
    q = db.query(Product).filter(Product.is_deleted == 0, Product.status == "ON_SALE")
    if category_id:
        q = q.filter(Product.category_id == category_id)
    if keyword:
        q = q.filter(Product.title.like(f"%{keyword}%"))
    if sort == "price_asc":
        # need join sku min price; simplified: no sorting by price now
        pass
    total = q.count()
    rows = q.order_by(Product.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    data = [{
        "id": r.id, "title": r.title, "subtitle": r.subtitle, "cover_image": r.cover_image, "status": r.status, "category_id": r.category_id
    } for r in rows]
    return ok({"total": total, "list": data})

@router.get("/products/{pid}")
def product_detail(pid: int, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == pid).first()
    if not p:
        return ok(None)
    return ok({
        "id": p.id, "title": p.title, "subtitle": p.subtitle, "description": p.description, "cover_image": p.cover_image, "status": p.status, "category_id": p.category_id
    })

@router.get("/products/{pid}/skus")
def product_skus(pid: int, db: Session = Depends(get_db)):
    rows = db.query(ProductSKU).filter(ProductSKU.product_id == pid, ProductSKU.is_active == 1).all()
    return ok([{
        "id": r.id, "sku_code": r.sku_code, "color": r.color, "size": r.size, "price": float(r.price), "stock": r.stock, "image": r.image
    } for r in rows])