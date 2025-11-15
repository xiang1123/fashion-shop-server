from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from fastapi.responses import PlainTextResponse, RedirectResponse, HTMLResponse
from app.db.session import get_db
from app.services.payment import create_alipay_wap_payment, handle_alipay_notify
from app.schemas.common import ok
from app.core.security import get_current_user
from app.core.config import settings
from app.models.users import User
from app.models.orders import Order
from app.models.payments import Payment

router = APIRouter()
router_public_root = APIRouter()

@router.post("/pay/alipay/{order_id}")
def alipay_wap(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        return {"code": 1, "message": "订单不存在"}
    if order.status != "UNPAID":
        return {"code": 1, "message": "订单状态不允许发起支付"}

    pay_url = create_alipay_wap_payment(db, order)
    if not pay_url:
        # 表示查询到该 out_trade_no 在支付宝侧已支付或已关闭
        # 前端应刷新订单列表展示最新状态
        return ok({"pay_url": "", "hint": "订单状态已更新，请刷新订单列表"})
    return ok({"pay_url": pay_url})

@router_public_root.post("/alipay/notify")
async def alipay_notify_root(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    print("Alipay notify headers:", dict(request.headers))
    print("Alipay notify raw:", raw.decode("utf-8", errors="ignore"))

    form = dict(await request.form())
    print("【支付宝异步通知】", form)
    result = handle_alipay_notify(db, form)
    return PlainTextResponse("success" if result == "success" else "fail")

@router_public_root.get("/alipay/return")
async def alipay_return_root(request: Request, db: Session = Depends(get_db)):
    params = dict(request.query_params)
    print("【支付宝用户回跳】", params)

    out_trade_no = params.get("out_trade_no")
    trade_no = params.get("trade_no")

    order_id = None
    if out_trade_no:
        payment = db.query(Payment).filter(Payment.out_trade_no == out_trade_no).first()
        if payment:
            order_id = payment.order_id

    target = getattr(settings, "CLIENT_PAY_RESULT_URL", None)
    if not target:
        html = f"""
        <html><head><meta charset="utf-8" />
        <title>支付完成</title></head>
        <body>
          <p>支付完成，请以订单状态为准。</p>
          <p>订单号: {out_trade_no or ''}</p>
          <p>支付宝交易号: {trade_no or ''}</p>
        </body></html>
        """
        return HTMLResponse(html, status_code=200)

    qs = []
    if order_id is not None:
        qs.append(f"orderId={order_id}")
    if out_trade_no:
        qs.append(f"outTradeNo={out_trade_no}")
    if trade_no:
        qs.append(f"tradeNo={trade_no}")
    if qs:
        target = f"{target}{'&' if '?' in target else '?'}{'&'.join(qs)}"

    return RedirectResponse(target, status_code=302)