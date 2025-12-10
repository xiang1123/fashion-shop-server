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
    自定义 ID 生成逻辑：
    1. 一级分类：取当前最大的一级 ID + 1 (如 5 -> 6)
    2. 二级分类：父ID + 自增序号 (如父1 -> 11, 12... 19, 110)
    """
    # --- 情况 A：一级分类 ---
    if parent_id is None:
        # 查找当前最大的 id (且 parent_id 为空的)
        last_root = db.query(Category).filter(Category.parent_id == None).order_by(Category.id.desc()).first()

        if not last_root:
            return 1  # 第一个分类，ID 为 1

        # 简单递增：5 -> 6
        next_id = last_root.id + 1

        # 安全检查：防止计算出的 ID 6 已经被其他脏数据占用了
        while db.query(Category).filter(Category.id == next_id).first():
            next_id += 1

        return next_id

    # --- 情况 B：二级分类 ---
    else:
        # 先获取父级信息
        parent = db.query(Category).filter(Category.id == parent_id).first()
        if not parent:
            raise ValueError("父分类不存在")

        pid_str = str(parent_id)  # 例如 "1"

        # 找出该父级下所有的子分类
        children = db.query(Category).filter(Category.parent_id == parent_id).all()

        max_seq = 0
        for child in children:
            cid_str = str(child.id)
            # 逻辑校验：子ID必须以父ID开头 (如 11 以 1 开头)
            if cid_str.startswith(pid_str) and len(cid_str) > len(pid_str):
                try:
                    # 截取后缀部分。例如 ID 11 -> 后缀 "1"; ID 110 -> 后缀 "10"
                    suffix = cid_str[len(pid_str):]
                    seq = int(suffix)
                    if seq > max_seq:
                        max_seq = seq
                except ValueError:
                    continue  # 忽略不符合规则的脏数据

        # 下一个序号：例如当前最大是 9，下一个是 10
        next_seq = max_seq + 1

        # 拼接生成新 ID：Parent "1" + Seq "10" -> 110
        new_id_str = f"{pid_str}{next_seq}"
        new_id = int(new_id_str)

        # 安全检查：查重
        while db.query(Category).filter(Category.id == new_id).first():
            next_seq += 1
            new_id = int(f"{pid_str}{next_seq}")

        return new_id


@router.get("/categories")
def list_categories(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    # 按 ID 排序，这样 1, 11, 12, 2 会比较整齐
    rows = db.query(Category).order_by(Category.id.asc()).all()
    # 如果有 code 字段就返回，没有就不返回，不影响 id 的使用
    res = []
    for r in rows:
        item = {
            "id": r.id,
            "parent_id": r.parent_id,
            "name": r.name,
            "level": r.level,
            "sort_order": r.sort_order,
            "is_visible": r.is_visible
        }
        if hasattr(r, 'code'):
            item['code'] = r.code
        res.append(item)
    return ok(res)


@router.post("/categories")
def create_category(req: CategoryCreate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    try:
        # 1. 计算我们想要的 ID
        custom_id = generate_custom_id(db, req.parent_id)
    except ValueError as e:
        return err(str(e))

    # 2. 强制将 ID 写入数据库
    # 即使数据库是 AUTO_INCREMENT，指定了 id 后，数据库就会使用我们给的值
    c = Category(
        id=custom_id,  # <--- 关键点：强制赋值
        parent_id=req.parent_id,
        name=req.name,
        level=req.level,
        sort_order=req.sort_order,
        is_visible=req.is_visible,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # 如果你的模型里有 code 字段，也可以顺便存一下，保持一致
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