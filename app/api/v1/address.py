from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.users import User
from app.models.addresses import Address
from app.schemas.address import AddressCreate, AddressUpdate
from app.schemas.common import ok, err

router = APIRouter()

@router.get("/addresses")
def list_addresses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Address).filter(Address.user_id == user.id).order_by(Address.id.desc()).all()
    return ok([{
        "id": r.id,
        "contact_name": r.contact_name,
        "contact_phone": r.contact_phone,
        "province": r.province,
        "city": r.city,
        "district": r.district,
        "detail": r.detail,
        "is_default": bool(r.is_default),
    } for r in rows])

@router.post("/addresses")
def create_address(req: AddressCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    addr = Address(
        user_id=user.id,
        contact_name=req.contact_name,
        contact_phone=req.contact_phone,
        province=req.province,
        city=req.city,
        district=req.district,
        detail=req.detail,
        is_default=1 if req.is_default else 0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return ok({"id": addr.id})

@router.patch("/addresses/{addr_id}")
def update_address(addr_id: int, req: AddressUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    addr = db.query(Address).filter(Address.id == addr_id, Address.user_id == user.id).first()
    if not addr:
        return err("地址不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(addr, k, v if k != "is_default" else (1 if v else 0))
    addr.updated_at = datetime.now()
    db.commit()
    return ok(True)

@router.delete("/addresses/{addr_id}")
def delete_address(addr_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    addr = db.query(Address).filter(Address.id == addr_id, Address.user_id == user.id).first()
    if not addr:
        return err("地址不存在")
    db.delete(addr)
    db.commit()
    return ok(True)