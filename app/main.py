from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, address, product, cart, orders, pay_alipay, shipment
from app.api.v1.admin import admin_auth, dashboard, admin_products, admin_orders, admin_categories, admin_banners, admin_users, admin_stock
from app.core.config import settings

def create_app():
    app = FastAPI(title=settings.APP_NAME)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
    app.include_router(address.router, prefix="/api/v1", tags=["addresses"])
    app.include_router(product.router, prefix="/api/v1", tags=["products"])
    app.include_router(cart.router, prefix="/api/v1", tags=["cart"])
    app.include_router(orders.router, prefix="/api/v1", tags=["orders"])
    app.include_router(shipment.router, prefix="/api/v1", tags=["shipment"])

    # 发起支付（需要登录）
    app.include_router(pay_alipay.router, prefix="/api/v1", tags=["pay"])
    # 公开：根级回调与回跳
    app.include_router(pay_alipay.router_public_root, tags=["pay-public"])

    app.include_router(admin_auth.router, prefix="/admin/api/v1", tags=["admin-auth"])
    app.include_router(dashboard.router, prefix="/admin/api/v1", tags=["dashboard"])
    app.include_router(admin_categories.router, prefix="/admin/api/v1", tags=["admin-categories"])
    app.include_router(admin_products.router, prefix="/admin/api/v1", tags=["admin-products"])
    app.include_router(admin_stock.router, prefix="/admin/api/v1", tags=["admin-stock"])
    app.include_router(admin_orders.router, prefix="/admin/api/v1", tags=["admin-orders"])
    app.include_router(admin_banners.router, prefix="/admin/api/v1", tags=["admin-banners"])
    app.include_router(admin_users.router, prefix="/admin/api/v1", tags=["admin-users"])

    @app.on_event("startup")
    async def show_routes():
        for r in app.routes:
            deps = getattr(r, "dependencies", []) or []
            print(r.path, [getattr(d.dependency, "__name__", str(d.dependency)) for d in deps])
        print("ALIPAY_NOTIFY_URL:", settings.ALIPAY_NOTIFY_URL)
        print("ALIPAY_RETURN_URL:", settings.ALIPAY_RETURN_URL)
        print("CLIENT_PAY_RESULT_URL:", getattr(settings, "CLIENT_PAY_RESULT_URL", None))
        print("ALIPAY_GATEWAY:", settings.ALIPAY_GATEWAY)

    return app

app = create_app()