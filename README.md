# fashion-shop 后端项目 README

一个基于 FastAPI + SQLAlchemy + MySQL 的服装电商后端，覆盖用户端与后台管理端的核心功能：注册登录、商品与分类、购物车、订单与库存预占、支付宝沙盒 WAP 支付、发货记录等，并已开启跨域。

- 代码目录：`server/`
- API 前缀
  - H5 用户端：`/api/v1`
  - 后台管理端：`/admin/api/v1`

## 技术栈

- Web 框架：FastAPI
- ORM：SQLAlchemy 2.x
- 数据库：MySQL 8.x（驱动 `pymysql`）
- 鉴权：JWT（`HS256`）
- 密码：bcrypt（`passlib`）
- 支付：支付宝沙盒 WAP（RSA2 加签）
- 缓存：Redis（可选，用于后续扩展）
- 运行：uvicorn

## 目录结构

```text
server/
├─ requirements.txt
├─ .env.example
├─ README.md
├─ db/
│  └─ schema.sql
└─ app/
   ├─ __init__.py
   ├─ main.py
   ├─ core/
   │  ├─ __init__.py
   │  ├─ config.py
   │  └─ security.py
   ├─ db/
   │  ├─ __init__.py
   │  └─ session.py
   ├─ models/
   │  ├─ __init__.py
   │  ├─ users.py
   │  ├─ admins.py
   │  ├─ addresses.py
   │  ├─ categories.py
   │  ├─ products.py
   │  ├─ skus.py
   │  ├─ banners.py
   │  ├─ carts.py
   │  ├─ orders.py
   │  ├─ inventory_locks.py
   │  ├─ payments.py
   │  └─ shipments.py
   ├─ schemas/
   │  ├─ __init__.py
   │  ├─ common.py
   │  ├─ auth.py
   │  ├─ address.py
   │  ├─ product.py
   │  ├─ cart.py
   │  ├─ order.py
   │  ├─ pay.py
   │  └─ admin.py
   ├─ services/
   │  ├─ __init__.py
   │  ├─ order.py
   │  └─ payment.py
   ├─ utils/
   │  ├─ __init__.py
   │  └─ alipay.py
   └─ api/
      ├─ __init__.py
      ├─ v1/
      │  ├─ __init__.py
      │  ├─ auth.py
      │  ├─ address.py
      │  ├─ product.py
      │  ├─ cart.py
      │  ├─ orders.py
      │  ├─ pay_alipay.py
      │  └─ shipment.py
      └─ admin/
         ├─ __init__.py
         ├─ admin_auth.py
         ├─ admin_products.py
         ├─ admin_orders.py
         ├─ admin_categories.py
         ├─ admin_banners.py
         ├─ admin_users.py
         ├─ dashboard.py
         └─ admin_stock.py
```

## 环境准备

- Python 3.10+
- MySQL 8.x（已创建数据库与用户）
  - 数据库 IP：`8.216.6.228`
  - 用户名：`fashion_shop` 密码：`123456`
  - 数据库名：`fashion_shop`
- Redis（本地默认 `redis://localhost:6379/0`）
- 支付宝沙盒
  - `APP_ID`：`9021000156667787`
  - 网关：`https://openapi-sandbox.dl.alipaydev.com/gateway.do`
  - 内网穿透地址（供支付宝回调访问）：`http://r692cf64.natappfree.cc`

## 安装与运行

1) 安装依赖

```bash
cd server
pip install -r requirements.txt
```

2) 初始化数据库表

- 在 MySQL 中执行 `db/schema.sql`（已包含所有核心表与约束）：
```bash
mysql -h 8.216.6.228 -u fashion_shop -p
# 输入密码 123456
# 在 MySQL 控制台执行：
SOURCE /absolute/path/to/server/db/schema.sql;
```

3) 配置环境变量

- 复制 `.env.example` 到 `.env`，并填入你的配置：
```env
APP_NAME=fashion-shop
APP_ENV=dev
APP_DEBUG=true
APP_SECRET_KEY=super-secret-change-me
ACCESS_TOKEN_EXPIRE_MINUTES=43200

ALLOW_ORIGINS=*

DB_HOST=8.216.6.228
DB_PORT=3306
DB_USER=fashion_shop
DB_PASSWORD=123456
DB_NAME=fashion_shop

REDIS_URL=redis://localhost:6379/0

ALIPAY_APP_ID=9021000156667787
ALIPAY_GATEWAY=https://openapi-sandbox.dl.alipaydev.com/gateway.do
# 注意：应用私钥必须为 PEM 格式（见下方说明）
ALIPAY_APP_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCgKaB45EuqAa5s
...（每行 64 字符分行）...
...你的私钥内容...
-----END PRIVATE KEY-----"
ALIPAY_PUBLIC_KEY="MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAiFSnD38eZvvhELimZq/AqZT5ZhblpOjNdehgwQ0FkdUjJramDDpKQEJsGtcHSHJr/FQT3LSOHhzwhyoJkbwnRL/p9Zfbz9mOMsTV7w6ExmJE9T/lz7dZJFOYQO4pcHUhLpYvYMUhyeDKiZbMnv1eDaoStf2LMEqFZhDBIoqMqeuNjeQ/avLjPj/gSYyrvtuf+4LrNiQRQDgswdEFF0CvGkaKJGSWLbsmiDFrNAEaQq5NBxRmA/V85WWcRg8Bv3ETsLd4pdRnF9GCe//dN/zaP+FYWaA/csS8beArGWTYRmpDGAoGN0cpj3RC+jq1hjp51YqJmDLtKJkKP7ielxm62wIDAQAB"
ALIPAY_NOTIFY_URL=http://r692cf64.natappfree.cc/api/v1/pay/alipay/notify
ALIPAY_RETURN_URL=http://r692cf64.natappfree.cc/api/v1/pay/alipay/return
```

4) 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

5) 访问接口

- Swagger 文档（默认开启）：`http://localhost:8000/docs`
- 用户端示例：`POST /api/v1/auth/register`、`POST /api/v1/auth/login`
- 管理端示例：`POST /admin/api/v1/auth/login`

## 支付宝沙盒配置说明

- 公钥：你提供的是一行 Base64，无需处理，代码会自动包裹成 PEM。
- 应用私钥：必须为 PEM 格式。若你只有一行 Base64（`MIIEvQ...`），请手动包裹：
  - 在私钥前后添加
    - `-----BEGIN PRIVATE KEY-----`
    - `-----END PRIVATE KEY-----`
  - 中间内容按每行 64 字符分行。
- `notify_url` 必须公网可达。确保内网穿透（`http://r692cf64.natappfree.cc`）已绑定到你本机的 `http://localhost:8000`，并且路径 `/api/v1/pay/alipay/notify` 对外可访问。
- 发起支付接口：
  - `POST /api/v1/pay/alipay/{order_id}` 返回 `pay_url`，前端直接跳转该 URL 至沙盒收银台。
- 异步通知：
  - 支付宝会 `POST` 到 `ALIPAY_NOTIFY_URL`，服务端验签成功后将订单更新为 `PAID` 并返回 `success`。
- 用户回跳：
  - `GET /api/v1/pay/alipay/return` 仅用于展示支付结果，实际结果以服务端订单状态为准。

## 管理员初始化

- 插入一条管理员（示例密码 `admin123` 的 bcrypt）：
```sql
INSERT INTO admins (username, password_hash, role, status, created_at, updated_at)
VALUES ('admin',
'$2b$12$PEbqSgFh1YfT6kH4tQj1FegGQ1pWvJzK2O1fQpDlb9p3sKfTqa5Gq',  -- admin123
'SUPER', 'ACTIVE', NOW(), NOW());
```

- 登录：
  - `POST /admin/api/v1/auth/login`
  - Body: `{"username":"admin","password":"admin123"}`

## 核心功能与接口速览

- 认证与用户（H5）
  - `POST /api/v1/auth/register`、`POST /api/v1/auth/login`
  - `GET /api/v1/auth/profile`、`PATCH /api/v1/auth/profile`
  - 鉴权使用 `Authorization: Bearer <token>`
- 地址管理
  - `GET /api/v1/addresses`、`POST /api/v1/addresses`
  - `PATCH /api/v1/addresses/{id}`、`DELETE /api/v1/addresses/{id}`
- 商品与分类
  - `GET /api/v1/banners`、`GET /api/v1/categories`
  - `GET /api/v1/products`、`GET /api/v1/products/{id}`
  - `GET /api/v1/products/{id}/skus`
- 购物车
  - `GET /api/v1/cart`
  - `POST /api/v1/cart/items`、`PATCH /api/v1/cart/items/{item_id}`、`DELETE /api/v1/cart/items/{item_id}`
  - `POST /api/v1/cart/clear`
- 订单与库存
  - `POST /api/v1/orders`（购物车下单，库存预占）
  - `GET /api/v1/orders`、`GET /api/v1/orders/{id}`
  - `POST /api/v1/orders/{id}/cancel`（释放预占）
  - `POST /api/v1/orders/{id}/confirm`
- 支付（支付宝沙盒 WAP）
  - `POST /api/v1/pay/alipay/{order_id}` 获取跳转 URL
  - `POST /api/v1/pay/alipay/notify` 异步通知验签与状态更新
  - `GET /api/v1/pay/alipay/return` 用户回跳页面数据
- 物流（核心阶段手工录入）
  - `GET /api/v1/orders/{id}/shipment`
- 后台管理
  - 分类：`/admin/api/v1/categories`（GET/POST/PATCH/DELETE）
  - 商品与 SKU：`/admin/api/v1/products`、`/admin/api/v1/products/{id}/skus`
  - 库存：`GET/PATCH /admin/api/v1/skus/{id}/stock`
  - 订单：`/admin/api/v1/orders`、`/admin/api/v1/orders/{id}`、`POST /admin/api/v1/orders/{id}/ship`、`/cancel`
  - Banner：`/admin/api/v1/banners`
  - 用户：`/admin/api/v1/users`

## 跨域

- 已启用 `CORSMiddleware`，默认 `ALLOW_ORIGINS=*`。可在 `.env` 中配置为逗号分隔的域名列表，如：
```env
ALLOW_ORIGINS=http://localhost:5173,http://localhost:5174
```

## 订单与库存策略

- 预占时机：下单即扣减 `SKU.stock` 并生成 `inventory_locks` 记录，状态为 `LOCKED`。
- 取消订单：将锁标记为 `RELEASED` 并加回库存。
- 支付成功：将锁标记为 `CONSUMED`（库存已在预占阶段扣减）。
- 超时释放：`inventory_locks.expires_at` 已记录，当前示例未实现定时自动释放（可用定时任务扫描实现）。

## 常见问题

- 支付验签失败：
  - 确认 `ALIPAY_APP_PRIVATE_KEY` 为 PEM 格式（带 `BEGIN/END PRIVATE KEY`），行宽 64。
  - 公钥一行 Base64 可直接使用；代码内部会包裹为 PEM。
  - 确认沙盒网关地址：`https://openapi-sandbox.dl.alipaydev.com/gateway.do`。
- 支付回调未达到：
  - 检查内网穿透是否连通，`ALIPAY_NOTIFY_URL` 是否公网可达。
  - 服务端端口与路由是否正确映射。
- MySQL 连接失败：
  - 检查远程 IP、用户名/密码、端口 3306 是否放行。
  - 确认 `.env` 中配置与实际一致。
- JWT 鉴权：
  - 请求头需携带 `Authorization: Bearer <token>`。

## 示例调用

- 注册并登录（返回 `token`）：
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"u1@test.com","password":"p@ss123"}'

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"u1@test.com","password":"p@ss123"}'
```

- 发起支付：
```bash
# 假设已登录，拿到 token 与 order_id
curl -X POST http://localhost:8000/api/v1/pay/alipay/123 \
  -H "Authorization: Bearer <token>"
# 返回 pay_url，前端跳转该链接
```

## 部署建议

- 使用 `gunicorn` + `uvicorn.workers.UvicornWorker` 或者 `uvicorn` 多进程模式。
- 配置 HTTPS（尤其涉支付场景）。
- `.env` 中的 `APP_SECRET_KEY` 请替换为强随机值。
- 数据库连接池与超时参数可根据流量调整。
- 增加请求日志、中间件统一异常处理、幂等控制与审计日志。
