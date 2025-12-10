from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.categories import Category
from app.schemas.admin import CategoryCreate, CategoryUpdate
from app.schemas.common import ok, err

router = APIRouter()


def generate_custom_id(db: Session, parent_id: int | None) -> int:
    """
    新版 ID 生成逻辑 (避免冲突):
    1. 一级分类：在 1~99 之间找空缺，或者取最大值+1
    2. 二级分类：父ID * 100 + 序号 (如 1 -> 101, 102...)
    """
    # --- 情况 A：一级分类 (使用 1-99 范围) ---
    if parent_id is None:
        # 简单策略：查找当前最大的一级 ID + 1
        last_root = db.query(Category).filter(Category.parent_id == None).order_by(Category.id.desc()).first()

        start_id = 1
        if last_root:
            # 如果当前最大是 10，下一个试 11
            start_id = last_root.id + 1

        # 循环向后找，直到找到一个没被占用的 ID
        # 这样即使 11 曾经被占用，现在搬走了，这里就能用 11 了
        while db.query(Category).filter(Category.id == start_id).first():
            start_id += 1

        return start_id

    # --- 情况 B：二级分类 (使用 Parent * 100 + Seq) ---
    else:
        # 例如 parent_id = 1, 我们希望生成 101, 102...
        # 例如 parent_id = 10, 我们希望生成 1001, 1002...
        base_id = parent_id * 100

        # 查找该父类下 ID 最大的子类
        last_child = db.query(Category).filter(
            Category.parent_id == parent_id,
            Category.id >= base_id  # 确保是新规则下的子类
        ).order_by(Category.id.desc()).first()

        if not last_child:
            new_id = base_id + 1  # 第一个子类：101
        else:
            new_id = last_child.id + 1  # 递增：102

        # 双重保险：查重
        while db.query(Category).filter(Category.id == new_id).first():
            new_id += 1

        return new_id


@router.get("/categories")
def list_categories(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    # 按照排序值升序排列
    rows = db.query(Category).order_by(Category.sort_order.asc()).all()
    return ok([{
        "id": r.id,
        "parent_id": r.parent_id,
        "name": r.name,
        "level": r.level,
        "sort_order": r.sort_order,
        "is_visible": r.is_visible
    } for r in rows])


@router.post("/categories")
def create_category(req: CategoryCreate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    # 1. 【核心修改】校验排序值是否重复
    # 查询在同一个 parent_id 下，是否已经存在相同的 sort_order
    duplicate_sort = db.query(Category).filter(
        Category.parent_id == req.parent_id,
        Category.sort_order == req.sort_order
    ).first()

    if duplicate_sort:
        # 如果存在，直接返回错误信息，前端会弹出提示
        return err(f"排序值 {req.sort_order} 已存在，排序不能重复")

    try:
        # 2. 计算自定义 ID
        custom_id = generate_custom_id(db, req.parent_id)
    except ValueError as e:
        return err(str(e))

    # 3. 创建分类
    c = Category(
        id=custom_id,
        parent_id=req.parent_id,
        name=req.name,
        level=req.level,
        sort_order=req.sort_order,
        is_visible=req.is_visible,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    if hasattr(Category, 'code'):
        c.code = str(custom_id)

    db.add(c)
    db.commit()
    db.refresh(c)
    return ok({"id": c.id})


@router.patch("/categories/{cid}")
def update_category(cid: int, req: CategoryUpdate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    c = db.query(Category).filter(Category.id == cid).first()
    if not c:
        return err("分类不存在")

    # 1. 【核心修改】如果是更新操作，也要校验排序值
    # 如果请求中包含 sort_order 或 parent_id，说明可能改变了排序或层级，需要检查冲突
    if req.sort_order is not None or req.parent_id is not None:
        # 确定新的父ID（如果请求没传，就用原来的）
        target_parent_id = req.parent_id if req.parent_id is not None else c.parent_id
        # 确定新的排序值
        target_sort_order = req.sort_order if req.sort_order is not None else c.sort_order

        # 查询是否有冲突（排除掉自己）
        duplicate_sort = db.query(Category).filter(
            Category.parent_id == target_parent_id,
            Category.sort_order == target_sort_order,
            Category.id != cid  # 排除自己
        ).first()

        if duplicate_sort:
            return err(f"排序值 {target_sort_order} 已存在，排序不能重复")

    # 2. 执行更新
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

    # 检查子分类
    children = db.query(Category).filter(Category.parent_id == cid).first()
    if children:
        return err("该分类下包含子分类，请先删除子分类")

    db.delete(c)
    db.commit()
    return ok(True)