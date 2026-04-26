from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from api import deps
from db import models
from db.models.email import Signature
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class SignatureCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    content_html: str = Field(..., max_length=500_000)  # 500KB 上限
    is_default: bool = False


class SignatureUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    content_html: Optional[str] = Field(default=None, max_length=500_000)
    is_default: Optional[bool] = None


class SignatureRead(BaseModel):
    id: int
    name: str
    content_html: str
    is_default: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=List[SignatureRead])
def list_signatures(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取用户所有签名"""
    return db.query(Signature).filter(Signature.user_id == current_user.id).all()


@router.post("/", response_model=SignatureRead)
def create_signature(
    data: SignatureCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """创建签名"""
    # 如果设为默认，取消其他默认签名
    if data.is_default:
        db.query(Signature).filter(
            Signature.user_id == current_user.id,
            Signature.is_default == True
        ).update({"is_default": False})
    
    sig = Signature(
        user_id=current_user.id,
        name=data.name,
        content_html=data.content_html,
        is_default=data.is_default
    )
    db.add(sig)
    db.commit()
    db.refresh(sig)
    logger.info(f"用户 {current_user.id} 创建签名: id={sig.id}, name={sig.name}")
    return sig


@router.put("/{sig_id}", response_model=SignatureRead)
def update_signature(
    sig_id: int,
    data: SignatureUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """更新签名"""
    sig = db.query(Signature).filter(
        Signature.id == sig_id,
        Signature.user_id == current_user.id
    ).first()
    if not sig:
        raise HTTPException(status_code=404, detail="签名不存在")
    
    if data.name is not None:
        sig.name = data.name
    if data.content_html is not None:
        sig.content_html = data.content_html
    if data.is_default is not None:
        if data.is_default:
            # 取消其他默认签名
            db.query(Signature).filter(
                Signature.user_id == current_user.id,
                Signature.id != sig_id,
                Signature.is_default == True
            ).update({"is_default": False})
        sig.is_default = data.is_default
    
    db.commit()
    db.refresh(sig)
    logger.info(f"用户 {current_user.id} 更新签名: id={sig_id}")
    return sig


@router.delete("/{sig_id}")
def delete_signature(
    sig_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """删除签名"""
    sig = db.query(Signature).filter(
        Signature.id == sig_id,
        Signature.user_id == current_user.id
    ).first()
    if not sig:
        raise HTTPException(status_code=404, detail="签名不存在")
    
    sig_name = sig.name
    db.delete(sig)
    db.commit()
    logger.info(f"用户 {current_user.id} 删除签名: id={sig_id}, name={sig_name}")
    return {"status": "success"}


@router.get("/default")
def get_default_signature(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取默认签名"""
    sig = db.query(Signature).filter(
        Signature.user_id == current_user.id,
        Signature.is_default == True
    ).first()
    if not sig:
        return {"signature": None}
    return {"signature": sig.content_html}