from datetime import datetime
from sqlalchemy.orm import Session
from app.models.orders import Order
from app.models.payments import Payment
from app.utils.alipay import build_wap_pay_url, ordered_query, verify_with_rsa2, alipay_api_request, alipay_extract_response
from app.core.config import settings

def create_alipay_wap_payment(db: Session, order: Order) -> str:
    out_trade_no = order.order_no

    # 先查本地是否已成功
    payment = db.query(Payment).filter(Payment.out_trade_no == out_trade_no).first()
    if payment and payment.status == "SUCCESS":
        # 已支付，直接返回一个空链接或自定义提示，由上层决定不再跳转收银台
        return ""

    # 主动对齐支付宝侧交易状态（避免重复支付或异常提示）
    query_payload = alipay_api_request("alipay.trade.query", {"out_trade_no": out_trade_no})
    query_resp = alipay_extract_response("alipay.trade.query", query_payload)
    if query_resp.get("code") == "10000":
        trade_status = query_resp.get("trade_status")
        trade_no = query_resp.get("trade_no")
        total_amount_resp = float(query_resp.get("total_amount", "0"))

        if not payment:
            # 建立 INIT 记录，便于后续状态同步
            payment = Payment(
                order_id=order.id,
                channel="ALIPAY",
                out_trade_no=out_trade_no,
                amount=order.amount_payable,
                status="INIT",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(payment)
            db.commit()

        # 金额一致性（仅在成功态时严格校验）
        def amount_ok():
            return abs(float(payment.amount) - total_amount_resp) <= 1e-6

        if trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
            if amount_ok():
                # 同步成功态到本地
                payment.status = "SUCCESS"
                payment.trade_no = trade_no
                payment.paid_at = datetime.now()
                payment.updated_at = datetime.now()

                order.status = "PAID"
                order.paid_at = datetime.now()
                order.updated_at = datetime.now()
                db.commit()
                # 返回空链接表示无需进入收银台，前端应提示“订单已支付”
                return ""
        elif trade_status == "TRADE_CLOSED":
            payment.status = "CLOSED"
            payment.updated_at = datetime.now()
            db.commit()
            # 返回空链接表示订单已关闭
            return ""

        # WAIT_BUYER_PAY 或其它情况：继续生成支付链接
    else:
        # 查询失败（网络问题或网关返回非 10000），可以继续生成支付链接
        pass

    # 到这里说明还未支付成功，生成收银台链接
    pay_url = build_wap_pay_url(out_trade_no, str(order.amount_payable), f"订单{order.order_no}")

    # 建立或更新 INIT 记录
    payment = db.query(Payment).filter(Payment.out_trade_no == out_trade_no).first()
    if not payment:
        payment = Payment(
            order_id=order.id,
            channel="ALIPAY",
            out_trade_no=out_trade_no,
            amount=order.amount_payable,
            status="INIT",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(payment)
        db.commit()
    return pay_url

def handle_alipay_notify(db: Session, payload: dict) -> str:
    sign = payload.get("sign")
    sign_type = payload.get("sign_type", "RSA2")
    if sign_type != "RSA2":
        return "fail"

    content = ordered_query(payload, exclude_sign_type=True)  # 排除 sign 与 sign_type
    if not verify_with_rsa2(content, sign):
        return "fail"

    app_id = payload.get("app_id")
    seller_id = payload.get("seller_id")
    if app_id != settings.ALIPAY_APP_ID:
        return "fail"
    if getattr(settings, "ALIPAY_SELLER_ID", None) and seller_id and seller_id != settings.ALIPAY_SELLER_ID:
        return "fail"

    out_trade_no = payload.get("out_trade_no")
    trade_status = payload.get("trade_status")
    trade_no = payload.get("trade_no")
    total_amount = float(payload.get("total_amount", "0"))

    payment = db.query(Payment).filter(Payment.out_trade_no == out_trade_no).first()
    if not payment:
        return "fail"

    order = db.query(Order).filter(Order.id == payment.order_id).first()
    if not order:
        return "fail"

    if abs(float(payment.amount) - total_amount) > 1e-6:
        return "fail"

    if payment.status == "SUCCESS" or order.status == "PAID":
        return "success"

    if trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        payment.status = "SUCCESS"
        payment.trade_no = trade_no
        payment.paid_at = datetime.now()
        payment.notify_payload = payload
        payment.updated_at = datetime.now()

        order.status = "PAID"
        order.paid_at = datetime.now()
        order.updated_at = datetime.now()
        db.commit()
        return "success"

    elif trade_status == "TRADE_CLOSED":
        payment.status = "CLOSED"
        payment.notify_payload = payload
        payment.updated_at = datetime.now()
        db.commit()
        return "success"

    return "fail"