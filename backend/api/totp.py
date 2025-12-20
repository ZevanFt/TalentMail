"""
两步验证 (2FA/TOTP) API
"""
import io
import base64
import pyotp
import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db import models
from db.database import get_db
from api import deps
from core.config import settings

router = APIRouter()


class Enable2FAResponse(BaseModel):
    """启用 2FA 响应"""
    secret: str
    qr_code: str  # Base64 编码的二维码图片
    provisioning_uri: str


class Verify2FARequest(BaseModel):
    """验证 2FA 请求"""
    code: str


class Disable2FARequest(BaseModel):
    """禁用 2FA 请求"""
    code: str
    password: str


@router.get("/status")
def get_2fa_status(
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    获取当前用户的 2FA 状态
    """
    return {
        "enabled": current_user.two_factor_enabled,
        "has_secret": current_user.totp_secret is not None
    }


@router.post("/setup", response_model=Enable2FAResponse)
def setup_2fa(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    设置 2FA - 生成密钥和二维码
    注意：此时还未启用 2FA，需要调用 /enable 接口验证后才启用
    """
    # 如果已经启用了 2FA，不允许重新设置
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA 已启用，请先禁用后再重新设置"
        )
    
    # 生成新的 TOTP 密钥
    secret = pyotp.random_base32()
    
    # 生成 provisioning URI（用于 Authenticator App 扫描）
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name=f"TalentMail ({settings.BASE_DOMAIN})"
    )
    
    # 生成二维码
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 将二维码转换为 Base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    # 临时保存密钥（但不启用）
    current_user.totp_secret = secret
    db.add(current_user)
    db.commit()
    
    return Enable2FAResponse(
        secret=secret,
        qr_code=f"data:image/png;base64,{qr_code_base64}",
        provisioning_uri=provisioning_uri
    )


@router.post("/enable")
def enable_2fa(
    request: Verify2FARequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    启用 2FA - 验证用户输入的验证码后启用
    """
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA 已启用"
        )
    
    if not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先调用 /setup 接口生成密钥"
        )
    
    # 验证验证码
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(request.code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误，请重试"
        )
    
    # 启用 2FA
    current_user.two_factor_enabled = True
    db.add(current_user)
    db.commit()
    
    return {"status": "success", "message": "两步验证已启用"}


@router.post("/disable")
def disable_2fa(
    request: Disable2FARequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    禁用 2FA - 需要验证当前验证码和密码
    """
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA 未启用"
        )
    
    # 验证密码
    from core.security import verify_password
    if not verify_password(request.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码错误"
        )
    
    # 验证验证码
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(request.code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误"
        )
    
    # 禁用 2FA
    current_user.two_factor_enabled = False
    current_user.totp_secret = None
    db.add(current_user)
    db.commit()
    
    return {"status": "success", "message": "两步验证已禁用"}


@router.post("/verify")
def verify_2fa(
    request: Verify2FARequest,
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    验证 2FA 验证码（用于测试）
    """
    if not current_user.two_factor_enabled or not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA 未启用"
        )
    
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(request.code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误"
        )
    
    return {"status": "success", "message": "验证码正确"}