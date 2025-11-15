from pydantic import BaseModel

class AlipayPayResp(BaseModel):
    pay_url: str