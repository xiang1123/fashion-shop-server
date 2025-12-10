from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.products import Product
from app.models.categories import Category
from app.models.skus import ProductSKU
from app.schemas.admin import ProductCreate, ProductUpdate, SKUCreate, SKUUpdate
from app.schemas.common import ok, err, PageResult

router = APIRouter()


# -----------------------------------------------------------------------------
# 商品管理 (Products)
# -----------------------------------------------------------------------------

@router.get("/products")
def list_products(
        page: int = 1,
        page_size: int = 10,
        q: Optional[str] = None,
        category_id: Optional[int] = None,
        db: Session = Depends(get_db),
        admin=Depends(get_current_admin)
):
    query = db.query(Product).filter(Product.is_deleted == 0)

    if q:
        query = query.filter(Product.title.like(f"%{q}%"))

    if category_id:
        query = query.filter(Product.category_id == category_id)

    query = query.order_by(desc(Product.created_at))

    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

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

    return ok(PageResult(total=total, list=data, page=page, page_size=page_size))


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
    p.is_deleted = 1
    p.updated_at = datetime.now()
    db.commit()
    return ok(True)


# -----------------------------------------------------------------------------
# SKU 管理 (SKUs)
# -----------------------------------------------------------------------------

@router.get("/products/{pid}/skus")
def list_skus(pid: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    # 只显示未删除的
    rows = db.query(ProductSKU).filter(
        ProductSKU.product_id == pid,
        ProductSKU.is_deleted == 0
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
    # 1. 查找是否存在冲突记录（可能是活的，也可能是已删除的）
    # 冲突来源有两个：SKU编码重复 OR 规格(颜色+尺码)重复

    # 查找 SKU 编码冲突
    conflict_code = db.query(ProductSKU).filter(ProductSKU.sku_code == req.sku_code).first()

    # 查找 规格 冲突 (同一商品下的颜色+尺码)
    conflict_variant = db.query(ProductSKU).filter(
        ProductSKU.product_id == pid,
        ProductSKU.color == req.color,
        ProductSKU.size == req.size
    ).first()

    # -------------------------------------------------------
    # 辅助函数：复活并更新记录
    # -------------------------------------------------------
    def resurrect_record(record, req_data):
        record.product_id = pid
        record.sku_code = req_data.sku_code  # 更新为新的编码
        record.color = req_data.color
        record.size = req_data.size
        record.price = req_data.price
        record.stock = req_data.stock
        record.image = req_data.image
        record.bar_code = req_data.bar_code
        record.is_active = req_data.is_active
        record.is_deleted = 0  # <--- 复活！
        record.updated_at = datetime.now()
        db.commit()
        db.refresh(record)
        return ok({"id": record.id})

    # 情况 A: 编码和规格都指向同一个旧记录 -> 直接复活
    if conflict_code and conflict_variant and conflict_code.id == conflict_variant.id:
        if conflict_code.is_deleted == 0:
            return err("SKU已存在")
        return resurrect_record(conflict_code, req)

    # 情况 B: 编码没冲突，但规格冲突了 (例如删除了 '灰色-L'，现在又加 '灰色-L' 但换了个编码)
    if not conflict_code and conflict_variant:
        if conflict_variant.is_deleted == 0:
            return err(f"该规格 '{req.color}-{req.size}' 已存在")
        # 复活旧规格，但使用新编码
        return resurrect_record(conflict_variant, req)

    # 情况 C: 编码冲突了，但规格没冲突 (例如删除了 'A01'，现在给新规格用 'A01')
    if conflict_code and not conflict_variant:
        if conflict_code.is_deleted == 0:
            return err(f"SKU编码 '{req.sku_code}' 已存在")
        # 复活旧编码记录，并把它的规格改成新的
        return resurrect_record(conflict_code, req)

    # 情况 D: 两边都冲突，且不是同一条记录 (极少见，数据打架了)
    if conflict_code and conflict_variant and conflict_code.id != conflict_variant.id:
        return err(
            f"数据冲突：编码 '{req.sku_code}' 和规格 '{req.color}-{req.size}' 分别被不同的旧数据占用，请更换编码或联系管理员清理数据。")

    # 情况 E: 全新数据 -> 正常插入
    try:
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
            is_deleted=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(s)
        db.commit()
        db.refresh(s)
        return ok({"id": s.id})
    except IntegrityError as e:
        db.rollback()
        # 万一并发或者漏网之鱼，捕获唯一索引错误
        return err("创建失败：SKU编码或规格可能已存在")
    except Exception as e:
        db.rollback()
        return err(f"系统错误: {str(e)}")


@router.patch("/skus/{sid}")
def update_sku(sid: int, req: SKUUpdate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    s = db.query(ProductSKU).filter(ProductSKU.id == sid).first()
    if not s:
        return err("SKU不存在")

    # 查重 (如果改了编码)
    if req.sku_code and req.sku_code != s.sku_code:
        conflict = db.query(ProductSKU).filter(
            ProductSKU.sku_code == req.sku_code,
            ProductSKU.id != sid
        ).first()
        if conflict:
            return err(f"SKU编码 '{req.sku_code}' 已被占用")

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

    # 软删除
    s.is_deleted = 1
    s.is_active = 0
    s.updated_at = datetime.now()

    db.commit()
    return ok({"msg": "SKU已删除"})