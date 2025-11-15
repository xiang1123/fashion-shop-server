import base64
import json
import urllib.parse
from datetime import datetime
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
from Crypto.PublicKey import RSA
from app.core.config import settings
import requests  # 新增：发起网关 API 请求

def ordered_query(params: dict, exclude_sign_type: bool = False) -> str:
    """
    - 请求侧：exclude_sign_type=False，仅排除 sign（sign_type 参与签名）
    - 通知侧：exclude_sign_type=True，排除 sign 与 sign_type
    """
    items = [
        (k, v)
        for k, v in params.items()
        if v is not None
        and k != "sign"
        and (not exclude_sign_type or k != "sign_type")
    ]
    items.sort()
    return "&".join(f"{k}={v}" for k, v in items)

def sign_with_rsa2(content: str) -> str:
    private_key = RSA.import_key(settings.ALIPAY_APP_PRIVATE_KEY)
    h = SHA256.new(content.encode("utf-8"))
    signature = pkcs1_15.new(private_key).sign(h)
    return base64.b64encode(signature).decode("utf-8")

def verify_with_rsa2(content: str, signature: str) -> bool:
    try:
        public_key = RSA.import_key(alipay_public_key_pem(settings.ALIPAY_PUBLIC_KEY))
        h = SHA256.new(content.encode("utf-8"))
        pkcs1_15.new(public_key).verify(h, base64.b64decode(signature))
        return True
    except Exception as e:
        print("支付宝验签失败：", e)
        return False

def alipay_public_key_pem(key: str) -> bytes:
    key_body = key.strip()
    if "BEGIN PUBLIC KEY" in key_body:
        return key_body.encode("utf-8")
    lines = ["-----BEGIN PUBLIC KEY-----"]
    for i in range(0, len(key_body), 64):
        lines.append(key_body[i:i+64])
    lines.append("-----END PUBLIC KEY-----")
    return "\n".join(lines).encode("utf-8")

def build_wap_pay_url(out_trade_no: str, total_amount: str, subject: str) -> str:
    params = {
        "app_id": settings.ALIPAY_APP_ID,
        "method": "alipay.trade.wap.pay",
        "format": "JSON",
        "return_url": settings.ALIPAY_RETURN_URL,  # 根级 NAT 域名，例如 http://xxx/alipay/return
        "notify_url": settings.ALIPAY_NOTIFY_URL,  # 根级 NAT 域名，例如 http://xxx/alipay/notify
        "charset": "utf-8",
        "sign_type": "RSA2",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "1.0",
        "biz_content": json.dumps({
            "out_trade_no": out_trade_no,
            "total_amount": str(total_amount),
            "subject": subject,
            "product_code": "QUICK_WAP_WAY"
        }, separators=(",", ":"))
    }
    content = ordered_query(params, exclude_sign_type=False)  # 仅排除 sign
    print("Alipay request sign content:", content)
    sign = sign_with_rsa2(content)
    params["sign"] = sign
    query = urllib.parse.urlencode(params)
    return f"{settings.ALIPAY_GATEWAY}?{query}"

# 新增：通用网关 API 请求（如 alipay.trade.query）
def alipay_api_request(method: str, biz_content: dict, timeout: int = 10) -> dict:
    params = {
        "app_id": settings.ALIPAY_APP_ID,
        "method": method,
        "format": "JSON",
        "charset": "utf-8",
        "sign_type": "RSA2",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "1.0",
        "biz_content": json.dumps(biz_content, separators=(",", ":"))
    }
    content = ordered_query(params, exclude_sign_type=False)  # 仅排除 sign
    params["sign"] = sign_with_rsa2(content)

    # 注意：支付宝网关支持 x-www-form-urlencoded POST
    resp = requests.post(settings.ALIPAY_GATEWAY, data=params, timeout=timeout)
    try:
        return resp.json()
    except Exception:
        print("支付宝网关返回非 JSON：", resp.status_code, resp.text[:200])
        return {}

def alipay_extract_response(method: str, payload: dict) -> dict:
    # 返回体键名为 method 名字用下划线拼接 + "_response"
    # 例如：alipay.trade.query -> alipay_trade_query_response
    key = method.replace(".", "_") + "_response"
    return payload.get(key, {})