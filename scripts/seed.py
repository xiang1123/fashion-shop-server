import sys
from datetime import datetime
from typing import Optional, List, Tuple

# 允许脚本直接从 server 根目录运行，导入 app 包
if __name__ == "__main__":
    sys.path.append(".")

from app.db.session import SessionLocal
from app.core.security import hash_password
from app.models.admins import Admin
from app.models.categories import Category
from app.models.products import Product
from app.models.skus import ProductSKU
from app.models.banners import Banner

now = datetime.now()

def get_or_create_admin(db, username: str, password: str, role: str = "SUPER") -> Admin:
    admin = db.query(Admin).filter(Admin.username == username).first()
    if admin:
        print(f"[admin] 已存在: {username}")
        return admin
    admin = Admin(
        username=username,
        password_hash=hash_password(password),
        role=role,
        status="ACTIVE",
        created_at=now,
        updated_at=now,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    print(f"[admin] 创建成功: {username}")
    return admin

def get_or_create_category(db, name: str, parent: Optional[Category] = None, level: int = 1, sort_order: int = 0, is_visible: int = 1) -> Category:
    q = db.query(Category).filter(Category.name == name)
    if parent:
        q = q.filter(Category.parent_id == parent.id)
    else:
        q = q.filter(Category.parent_id == None)  # noqa: E711
    cat = q.first()
    if cat:
        print(f"[category] 已存在: {name}")
        return cat
    cat = Category(
        parent_id=parent.id if parent else None,
        name=name,
        level=level,
        sort_order=sort_order,
        is_visible=is_visible,
        created_at=now,
        updated_at=now,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    print(f"[category] 创建成功: {name}")
    return cat

def get_or_create_product(
    db,
    title: str,
    category: Category,
    subtitle: Optional[str],
    description: Optional[str],
    cover_image: Optional[str],
    status: str = "ON_SALE",
) -> Product:
    p = db.query(Product).filter(Product.title == title, Product.is_deleted == 0).first()
    if p:
        print(f"[product] 已存在: {title}")
        return p
    p = Product(
        category_id=category.id,
        title=title,
        subtitle=subtitle,
        description=description,
        cover_image=cover_image,
        status=status,
        is_deleted=0,
        created_at=now,
        updated_at=now,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    print(f"[product] 创建成功: {title}")
    return p

def get_or_create_sku(
    db,
    product: Product,
    sku_code: str,
    color: Optional[str],
    size: Optional[str],
    price: float,
    stock: int,
    image: Optional[str] = None,
    bar_code: Optional[str] = None,
    is_active: int = 1,
) -> ProductSKU:
    s = db.query(ProductSKU).filter(ProductSKU.sku_code == sku_code).first()
    if s:
        print(f"[sku] 已存在: {sku_code}")
        return s
    s = ProductSKU(
        product_id=product.id,
        sku_code=sku_code,
        color=color,
        size=size,
        price=price,
        stock=stock,
        image=image,
        bar_code=bar_code,
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    print(f"[sku] 创建成功: {sku_code} (color={color}, size={size}, price={price}, stock={stock})")
    return s

def get_or_create_banner(db, image_url: str, link_url: Optional[str], sort_order: int = 0, is_active: int = 1) -> Banner:
    b = db.query(Banner).filter(Banner.image_url == image_url).first()
    if b:
        print(f"[banner] 已存在: {image_url}")
        return b
    b = Banner(
        image_url=image_url,
        link_url=link_url,
        sort_order=sort_order,
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    print(f"[banner] 创建成功: {image_url}")
    return b

def seed(db):
    # 1) 超级管理员
    get_or_create_admin(db, username="admin", password="admin123", role="SUPER")

    # 2) 分类
    men = get_or_create_category(db, "男装", level=1, sort_order=10)
    women = get_or_create_category(db, "女装", level=1, sort_order=20)
    men_tshirt = get_or_create_category(db, "T恤", parent=men, level=2, sort_order=11)
    men_outer = get_or_create_category(db, "外套", parent=men, level=2, sort_order=12)
    women_dress = get_or_create_category(db, "连衣裙", parent=women, level=2, sort_order=21)

    # 3) 商品 + SKU
    # 男装 T恤
    p1 = get_or_create_product(
        db,
        title="基础款纯棉短袖 T 恤",
        category=men_tshirt,
        subtitle="舒适透气 | 多色可选",
        description="精选纯棉面料，亲肤舒适，简约百搭。适合春夏秋穿着。",
        cover_image="https://images.unsplash.com/photo-1520975922321-48e0d912c3b3?w=1200&q=80",
        status="ON_SALE",
    )
    colors_sizes: List[Tuple[str, str]] = [
        ("白色", "S"), ("白色", "M"), ("白色", "L"), ("白色", "XL"),
        ("黑色", "S"), ("黑色", "M"), ("黑色", "L"), ("黑色", "XL"),
    ]
    for color, size in colors_sizes:
        sku_code = f"TSHIRT-001-{color[:2].upper()}-{size}"
        get_or_create_sku(
            db,
            product=p1,
            sku_code=sku_code,
            color=color,
            size=size,
            price=79.9,
            stock=100,
            image="https://images.unsplash.com/photo-1520975922321-48e0d912c3b3?w=800&q=80",
        )

    # 男装 外套
    p2 = get_or_create_product(
        db,
        title="休闲连帽外套",
        category=men_outer,
        subtitle="防风保暖 | 都市通勤",
        description="经典连帽设计，耐磨防风面料，适合春秋通勤与户外穿着。",
        cover_image="https://images.unsplash.com/photo-1512436991641-6745cdb1723f?w=1200&q=80",
        status="ON_SALE",
    )
    for size in ["M", "L", "XL"]:
        sku_code = f"OUTER-001-灰-{size}"
        get_or_create_sku(
            db,
            product=p2,
            sku_code=sku_code,
            color="灰色",
            size=size,
            price=199.0,
            stock=50,
            image="https://images.unsplash.com/photo-1512436991641-6745cdb1723f?w=800&q=80",
        )

    # 女装 连衣裙
    p3 = get_or_create_product(
        db,
        title="轻盈飘逸连衣裙",
        category=women_dress,
        subtitle="夏日新款 | 优雅显瘦",
        description="轻薄透气面料，裙摆灵动飘逸，适合日常与度假穿着。",
        cover_image="https://images.unsplash.com/photo-1479064555552-3ef4979f5535?w=1200&q=80",
        status="ON_SALE",
    )
    for color in ["粉色", "蓝色"]:
        for size in ["S", "M", "L"]:
            sku_code = f"DRESS-001-{color[:2].upper()}-{size}"
            get_or_create_sku(
                db,
                product=p3,
                sku_code=sku_code,
                color=color,
                size=size,
                price=269.0,
                stock=30,
                image="https://images.unsplash.com/photo-1479064555552-3ef4979f5535?w=800&q=80",
            )

    # 4) Banner
    get_or_create_banner(
        db,
        image_url="https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1400&q=80",
        link_url="/pages/product?id={}".format(p1.id),
        sort_order=1,
        is_active=1,
    )
    get_or_create_banner(
        db,
        image_url="https://images.unsplash.com/photo-1519741497674-611481c9b6fb?w=1400&q=80",
        link_url="/pages/product?id={}".format(p2.id),
        sort_order=2,
        is_active=1,
    )
    get_or_create_banner(
        db,
        image_url="https://images.unsplash.com/photo-1483985988355-763728e1935b?w=1400&q=80",
        link_url="/pages/product?id={}".format(p3.id),
        sort_order=3,
        is_active=1,
    )

    print("\n✅ 初始化完成")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()