"""
两步验证 (2FA/TOTP) API
"""
import io
import json
import base64
import secrets
import logging
import pyotp
import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.hash import bcrypt

from db import models
from db.database import get_db
from api import deps
from core.config import settings
from utils.rate_limit import totp_manage_limiter

logger = logging.getLogger(__name__)
router = APIRouter()

BACKUP_CODE_COUNT = 8  # 生成 8 个备份码


def _generate_backup_codes() -> tuple[list[str], list[str]]:
    """生成备份码，返回 (明文码列表, bcrypt哈希列表)"""
    plain_codes = []
    hashed_codes = []
    for _ in range(BACKUP_CODE_COUNT):
        # 生成 8 字符的随机码，格式化为 xxxx-xxxx
        raw = secrets.token_hex(4)  # 8 hex chars
        code = f"{raw[:4]}-{raw[4:]}"
        plain_codes.append(code)
        hashed_codes.append(bcrypt.hash(code))
    return plain_codes, hashed_codes


def _verify_backup_code(code: str, hashed_codes: list[str]) -> int:
    """验证备份码，返回匹配的索引（-1 表示不匹配）"""
    # 规范化输入：去除空格和横线后重新格式化
    normalized = code.strip().replace("-", "").replace(" ", "").lower()
    if len(normalized) == 8:
        # 尝试匹配 xxxx-xxxx 格式
        formatted = f"{normalized[:4]}-{normalized[4:]}"
    else:
        formatted = code.strip()

    for i, hashed in enumerate(hashed_codes):
        if bcrypt.verify(formatted, hashed):
            return i
    return -1


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
    # 速率限制
    if not totp_manage_limiter.allow(f"2fa_setup:{current_user.id}"):
        raise HTTPException(status_code=429, detail="操作过于频繁，请 5 分钟后再试")

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

    logger.info(f"[2FA] 用户 {current_user.email} 生成了 2FA 密钥")
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
    # 速率限制
    if not totp_manage_limiter.allow(f"2fa_enable:{current_user.id}"):
        raise HTTPException(status_code=429, detail="操作过于频繁，请 5 分钟后再试")

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
    
    # 生成备份恢复码
    plain_codes, hashed_codes = _generate_backup_codes()

    # 启用 2FA + 保存备份码
    current_user.two_factor_enabled = True
    current_user.backup_codes = json.dumps(hashed_codes)
    db.add(current_user)
    db.commit()

    logger.info(f"[2FA] 用户 {current_user.email} 成功启用两步验证，已生成 {BACKUP_CODE_COUNT} 个备份码")
    return {
        "status": "success",
        "message": "两步验证已启用",
        "backup_codes": plain_codes,
        "backup_codes_count": BACKUP_CODE_COUNT,
    }


@router.post("/disable")
def disable_2fa(
    request: Disable2FARequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    禁用 2FA - 需要验证当前验证码和密码
    """
    # 速率限制
    if not totp_manage_limiter.allow(f"2fa_disable:{current_user.id}"):
        raise HTTPException(status_code=429, detail="操作过于频繁，请 5 分钟后再试")

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
    
    # 禁用 2FA 并清除密钥和备份码
    current_user.two_factor_enabled = False
    current_user.totp_secret = None
    current_user.backup_codes = None
    db.add(current_user)
    db.commit()

    logger.info(f"[2FA] 用户 {current_user.email} 禁用了两步验证")
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


@router.post("/regenerate-backup-codes")
def regenerate_backup_codes(
    request: Verify2FARequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    重新生成备份恢复码 — 需要当前 TOTP 验证码确认身份
    """
    if not totp_manage_limiter.allow(f"2fa_regen:{current_user.id}"):
        raise HTTPException(status_code=429, detail="操作过于频繁，请 5 分钟后再试")

    if not current_user.two_factor_enabled or not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA 未启用")

    # 验证 TOTP 码
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(request.code, valid_window=1):
        raise HTTPException(status_code=400, detail="验证码错误，请重试")

    # 生成新的备份码
    plain_codes, hashed_codes = _generate_backup_codes()
    current_user.backup_codes = json.dumps(hashed_codes)
    db.add(current_user)
    db.commit()

    logger.info(f"[2FA] 用户 {current_user.email} 重新生成了备份恢复码")
    return {
        "status": "success",
        "message": "备份恢复码已重新生成",
        "backup_codes": plain_codes,
        "backup_codes_count": BACKUP_CODE_COUNT,
    }


@router.get("/backup-codes-remaining")
def get_backup_codes_remaining(
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取剩余备份码数量"""
    if not current_user.two_factor_enabled:
        return {"remaining": 0, "total": 0}

    remaining = 0
    if current_user.backup_codes:
        try:
            codes = json.loads(current_user.backup_codes)
            remaining = len(codes)
        except (json.JSONDecodeError, TypeError):
            pass

    return {"remaining": remaining, "total": BACKUP_CODE_COUNT}