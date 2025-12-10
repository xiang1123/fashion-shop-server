from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.categories import Category
from app.schemas.admin import CategoryCreate, CategoryUpdate
from app.schemas.common import ok, err

router = APIRouter()


def generate_category_code(db: Session, parent_id: int | None) -> str:
    """
    核心逻辑：生成分类编码
    规则：
    1. 如果是一级分类：查找当前最大的一级 code (如 "5")，+1 得到 "6"
    2. 如果是二级分类：查找父级 code (如 "1")，再找它最大的子 code (如 "19")
       - 如果没有子分类，直接拼接 "1" -> "11"
       - 如果有子分类，取后缀最大值 +1 -> "110"
    """
    if not parent_id:
        # --- 生成一级分类 Code ---
        # 查找所有一级分类，按 id 倒序取最后一个（也可以按 code 排序，但字符串排序需注意）
        last_cat = db.query(Category).filter(Category.parent_id == None).order_by(Category.id.desc()).first()

        if not last_cat or not last_cat.code.isdigit():
            return "1"

        # 简单递增：5 -> 6
        return str(int(last_cat.code) + 1)

    else:
        # --- 生成子分类 Code ---
        parent = db.query(Category).filter(Category.id == parent_id).first()
        if not parent or not parent.code:
            # 如果父类不存在或没有code，这属于异常情况，这里暂定一个默认值
            return str(datetime.now().strftime("%H%M%S"))

        # 查找该父类下的所有子类
        last_sub = db.query(Category).filter(Category.parent_id == parent_id).order_by(Category.id.desc()).first()

        if not last_sub:
            # 没有子类，这是第一个。父Code + "1"。例如 1 -> 11
            return f"{parent.code}1"

        # 有子类，解析子类 Code 的后缀。例如 19 -> 9， 110 -> 10
        # 假设规则严格是 Prefix + Suffix
        parent_len = len(parent.code)
        try:
            # 截取父code之后的字符串作为序号
            last_suffix_str = last_sub.code[parent_len:]
            last_suffix = int(last_suffix_str)
            # 序号 + 1
            new_suffix = last_suffix + 1
            return f"{parent.code}{new_suffix}"
        except ValueError:
            # 如果解析失败（比如旧数据格式不对），直接拼接时间戳防止报错
            return f"{parent.code}{datetime.now().strftime('%M%S')}"


@router.get("/categories")
def list_categories(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    rows = db.query(Category).order_by(Category.sort_order.asc()).all()
    # 返回数据中包含 code 字段供前端展示
    return ok([{
        "id": r.id,
        "code": r.code,  # 前端展示这个作为“分类编号”
        "parent_id": r.parent_id,
        "name": r.name,
        "level": r.level,
        "sort_order": r.sort_order,
        "is_visible": r.is_visible
    } for r in rows])


@router.post("/categories")
def create_category(req: CategoryCreate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    # 1. 自动计算 Code
    new_code = generate_category_code(db, req.parent_id)

    # 2. 检查 Code 是否重复 (双重保险)
    exist = db.query(Category).filter(Category.code == new_code).first()
    if exist:
        return err(f"生成编号冲突 ({new_code})，请重试")

    c = Category(
        parent_id=req.parent_id,
        name=req.name,
        code=new_code,  # 存入计算好的 Code
        level=req.level,
        sort_order=req.sort_order,
        is_visible=req.is_visible,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return ok({"id": c.id, "code": c.code})


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