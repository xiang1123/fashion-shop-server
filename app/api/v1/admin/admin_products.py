from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.products import Product
from app.models.categories import Category
from app.models.skus import ProductSKU
from app.schemas.admin import ProductCreate, ProductUpdate, SKUCreate, SKUUpdate
# 引入刚才定义的 PageResult
from app.schemas.common import ok, err, PageResult

router = APIRouter()


# -----------------------------------------------------------------------------
# 商品列表接口 (支持搜索、分页)
# -----------------------------------------------------------------------------
@router.get("/products")
def list_products(
        page: int = 1,  # 页码
        page_size: int = 10,  # 每页条数
        q: Optional[str] = None,  # 搜索关键词
        category_id: Optional[int] = None,  # 分类筛选
        db: Session = Depends(get_db),
        admin=Depends(get_current_admin)
):
    # 1. 基础查询
    query = db.query(Product).filter(Product.is_deleted == 0)

    # 2. 搜索逻辑 (解决"搜索功能没有实现"的问题)
    if q:
        query = query.filter(Product.title.like(f"%{q}%"))

    # 3. 分类筛选
    if category_id:
        query = query.filter(Product.category_id == category_id)

    # 4. 排序：按时间倒序
    query = query.order_by(desc(Product.created_at))

    # 5. 分页计算 (解决"翻页翻不过去"的问题)
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    # 6. 构造返回数据
    data = []
    for p in rows:
        cat_name = p.category.name if p.category else ""
        p_dict = {
            "id": p.id,
            "category_id": p.category_id,
            "category_name": cat_name,
            "title": p.title,
            "subtitle": p.subtitle,
            "description": p.description,
            "cover_image": p.cover_image,
            "status": p.status,
            "created_at": p.created_at,
            "updated_at": p.updated_at
        }
        data.append(p_dict)

    # 7. 返回分页结构 (前端收到 total 才会显示页码)
    return ok(PageResult(total=total, list=data, page=page, page_size=page_size))


# -----------------------------------------------------------------------------
# 创建商品接口 (不强制 SKU)
# -----------------------------------------------------------------------------
@router.post("/products")
def create_product(req: ProductCreate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    if req.category_id:
        cat = db.query(Category).filter(Category.id == req.category_id).first()
        if not cat:
            return err("所选分类不存在")

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
    p = db.query(Product).filter(Product.id == pid, Product.is_deleted == 0).first()
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

    # 软删除
    p.is_deleted = 1
    p.updated_at = datetime.now()
    db.commit()
    return ok(True)


# -----------------------------------------------------------------------------
# SKU 接口 (保持原样，防止前端报错)
# -----------------------------------------------------------------------------
@router.get("/products/{pid}/skus")
def list_skus(pid: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    rows = db.query(ProductSKU).filter(
        ProductSKU.product_id == pid,
        ProductSKU.is_deleted == 0  # <--- 只显示未删除的
    ).all()
    return ok([{
        "id": r.id,
        "sku_code": r.sku_code,
        "color": r.color,
        "size": r.size,
        "price": float(r.price),
        "stock": r.stock,
        "image": r.image,
        "bar_code": r.bar_code,
        "is_active": r.is_active
    } for r in rows])


@router.post("/products/{pid}/skus")
def create_sku(pid: int, req: SKUCreate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    if req.product_id != pid: pass
    s = ProductSKU(
        product_id=pid, sku_code=req.sku_code, color=req.color, size=req.size,
        price=req.price, stock=req.stock, image=req.image, bar_code=req.bar_code,
        is_active=req.is_active, created_at=datetime.now(), updated_at=datetime.now(),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return ok({"id": s.id})


@router.patch("/skus/{sid}")
def update_sku(sid: int, req: SKUUpdate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    s = db.query(ProductSKU).filter(ProductSKU.id == sid).first()
    if not s: return err("SKU不存在")
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

    # 【核心修改】不执行 db.delete(s)，而是标记状态
    s.is_deleted = 1  # 标记为已删除
    s.is_active = 0  # 同时禁用，确保不会被购买
    s.sku_code = f"{s.sku_code}_del_{int(datetime.now().timestamp())}"  # 可选：修改编码释放占用，防止同名无法再次创建

    s.updated_at = datetime.now()
    db.commit()

    return ok({"msg": "SKU已删除"})