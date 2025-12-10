from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
# 移除 asc 的直接导入，改用对象方法 .asc()
from app.db.session import get_db
from app.models.banners import Banner
from app.models.categories import Category
from app.models.products import Product
from app.models.skus import ProductSKU
from app.schemas.common import ok

router = APIRouter()


# ... (banners 和 categories 接口保持不变，省略以节省空间) ...
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
        "id": r.id, "parent_id": r.parent_id, "name": r.name, "level": r.level, "sort_order": r.sort_order,
        "is_visible": r.is_visible
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

    total = q.count()
    rows = q.order_by(Product.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    data = []
    for r in rows:
        # [逻辑优化] 获取默认 SKU，按价格升序排序
        # 使用 ProductSKU.price.asc() 这种写法兼容性更好
        default_sku = db.query(ProductSKU) \
            .filter(ProductSKU.product_id == r.id, ProductSKU.is_active == 1) \
            .order_by(ProductSKU.price.asc()) \
            .first()

        data.append({
            "id": r.id,
            "title": r.title,
            "subtitle": r.subtitle,
            "cover_image": r.cover_image,
            "status": r.status,
            "category_id": r.category_id,
            # 价格转换：Decimal -> float
            "price": float(default_sku.price) if default_sku else 0.00,
            "default_sku_id": default_sku.id if default_sku else None
        })

    return ok({"total": total, "list": data})


# ... (product_detail 和 product_skus 接口保持不变) ...
@router.get("/products/{pid}")
def product_detail(pid: int, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == pid).first()
    if not p:
        return ok(None)
    return ok({
        "id": p.id, "title": p.title, "subtitle": p.subtitle, "description": p.description,
        "cover_image": p.cover_image, "status": p.status, "category_id": p.category_id
    })


@router.get("/products/{pid}/skus")
def product_skus(pid: int, db: Session = Depends(get_db)):
    rows = db.query(ProductSKU).filter(ProductSKU.product_id == pid, ProductSKU.is_active == 1).all()
    return ok([{
        "id": r.id, "sku_code": r.sku_code, "color": r.color, "size": r.size, "price": float(r.price), "stock": r.stock,
        "image": r.image
    } for r in rows])