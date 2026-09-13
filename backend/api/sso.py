"""
SSO 单点登录 API — auth-center OAuth 2.0 授权码流程
"""
import logging
import secrets
from datetime import timedelta, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core import security
from core.config import settings
from db.database import get_db
from db.models.user import User, UserSession
from utils.sso_email import email_match_candidates, normalize_sso_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/sso", tags=["SSO"])


class SSOLoginResponse(BaseModel):
    redirect_url: str


class SSOCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None


class SSOCallbackResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


def _require_sso_enabled():
    """检查 SSO 是否启用"""
    if not settings.SSO_ENABLED:
        raise HTTPException(404, "SSO 未启用")
    if not settings.SSO_AUTH_CENTER_URL or not settings.SSO_CLIENT_ID:
        raise HTTPException(500, "SSO 配置不完整")


@router.get("/login")
def sso_login(request: Request):
    """发起 SSO 登录 — 重定向到 auth-center"""
    _require_sso_enabled()

    # 生成 state 参数防 CSRF
    state = secrets.token_urlsafe(32)

    # 构建 auth-center 登录 URL
    auth_url = (
        f"{settings.SSO_AUTH_CENTER_URL}/login"
        f"?client_id={settings.SSO_CLIENT_ID}"
        f"&redirect_uri={settings.SSO_REDIRECT_URI}"
        f"&state={state}"
    )

    return SSOLoginResponse(redirect_url=auth_url)


@router.post("/callback")
async def sso_callback(
    body: SSOCallbackRequest,
    db: Session = Depends(get_db),
):
    """
    SSO 回调 — 用授权码换取用户信息并创建本地会话。
    前端收到 auth-center 回调的 code 后，POST 到此端点。
    """
    _require_sso_enabled()

    # Step 1: 用授权码换取 auth-center 用户信息
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.SSO_AUTH_CENTER_URL}/api/sso/token",
                json={
                    "client_id": settings.SSO_CLIENT_ID,
                    "client_secret": settings.SSO_CLIENT_SECRET,
                    "redirect_uri": settings.SSO_REDIRECT_URI,
                    "code": body.code,
                },
            )
    except httpx.RequestError as e:
        logger.error(f"SSO token 交换请求失败: {e}")
        raise HTTPException(502, "无法连接认证中心")

    if resp.status_code != 200:
        detail = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        error_code = detail.get("detail", {}).get("error_code", "UNKNOWN") if isinstance(detail.get("detail"), dict) else "UNKNOWN"
        logger.warning(f"SSO token 交换失败: status={resp.status_code}, error={error_code}")
        raise HTTPException(401, f"SSO 认证失败: {error_code}")

    sso_data = resp.json()
    sso_user = sso_data.get("user", {})
    sso_user_id = sso_user.get("id")
    sso_username = sso_user.get("username", "")
    sso_display_name = sso_user.get("display_name", "")

    if not sso_user_id:
        raise HTTPException(502, "认证中心返回的用户信息不完整")

    # Step 2: 查找或创建本地用户
    user = db.query(User).filter(User.sso_user_id == sso_user_id).first()

    if not user:
        # 尝试通过邮箱匹配已有用户（兼容纯用户名与完整邮箱）
        for candidate in email_match_candidates(sso_username, settings.BASE_DOMAIN):
            user = db.query(User).filter(User.email == candidate).first()
            if user:
                user.sso_user_id = sso_user_id
                if sso_display_name and not user.display_name:
                    user.display_name = sso_display_name
                db.commit()
                logger.info(f"SSO: 已关联现有用户 {user.email} ← sso_id={sso_user_id}")
                break

    if not user:
        # 新 SSO 用户：自动创建
        # 注意：SSO 用户可以没有密码（password_hash 设为不可验证的占位符）
        email_local = normalize_sso_email(sso_username, sso_user_id, settings.BASE_DOMAIN)

        user = User(
            email=email_local,
            password_hash="!SSO_USER_NO_PASSWORD",  # 不可通过密码登录
            display_name=sso_display_name or sso_username,
            sso_user_id=sso_user_id,
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"SSO: 自动创建新用户 {user.email}, sso_id={sso_user_id}")

        # 在 mailserver 中创建对应邮箱（随机密码，SSO 用户经 JWT 使用 Web/SMTP 代理）
        try:
            from core.mailserver_sync import create_mail_user
            mail_password = secrets.token_urlsafe(24)
            if not create_mail_user(user.email, mail_password):
                logger.warning(f"SSO: mailserver 创建邮箱失败（登录不受影响）: {user.email}")
        except Exception as e:
            logger.error(f"SSO: mailserver 创建邮箱异常（登录不受影响）: {e}")

    # Step 3: 创建会话和 JWT token
    session = UserSession(
        user_id=user.id,
        device_name="SSO Login",
        ip_address="sso",
        is_active=True,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email, "session_id": session.id},
        expires_delta=access_token_expires,
    )

    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = security.create_refresh_token(
        data={"sub": user.email, "session_id": session.id},
        expires_delta=refresh_token_expires,
    )

    logger.info(f"SSO: 用户 {user.email} 登录成功, session_id={session.id}")

    return SSOCallbackResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
            "sso_user_id": user.sso_user_id,
        },
    )


@router.get("/status")
def sso_status():
    """检查 SSO 是否启用（前端用来决定是否显示 SSO 按钮）"""
    return {
        "enabled": settings.SSO_ENABLED,
        "auth_center_url": settings.SSO_AUTH_CENTER_URL if settings.SSO_ENABLED else None,
        "client_id": settings.SSO_CLIENT_ID if settings.SSO_ENABLED else None,
    }


class SSOIntrospectRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None


class SSOIntrospectResponse(BaseModel):
    active: bool
    mfa_enabled: bool = False
    display_name: Optional[str] = None
    local_email: Optional[str] = None
    sso_user_id: Optional[str] = None


@router.post("/introspect", response_model=SSOIntrospectResponse)
async def sso_introspect(
    body: SSOIntrospectRequest,
    db: Session = Depends(get_db),
):
    """
    查询用户在认证中心是否仍有有效会话。

    用途：单点登出前校验、关键操作二次确认。
    入参可传 Auth Center username，或 TalentMail 本地邮箱（自动取 sso_user_id）。
    """
    _require_sso_enabled()

    username = (body.username or "").strip()
    if not username and body.email:
        user = db.query(User).filter(User.email == body.email.strip()).first()
        if user and user.sso_user_id:
            # Auth Center introspect 按 username 查询；本地存的是 sso id
            # 若 username 就是邮箱前缀/完整名，优先用完整邮箱；否则用 sso_user_id
            username = user.email
        elif user:
            return SSOIntrospectResponse(active=False, local_email=user.email)
    if not username:
        raise HTTPException(400, "请提供 username 或 email")

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                f"{settings.SSO_AUTH_CENTER_URL}/api/sso/introspect",
                json={
                    "client_id": settings.SSO_CLIENT_ID,
                    "client_secret": settings.SSO_CLIENT_SECRET or "",
                    "username": username,
                },
            )
    except httpx.RequestError as e:
        logger.error(f"SSO introspect 请求失败: {e}")
        raise HTTPException(502, "无法连接认证中心")

    if resp.status_code != 200:
        raise HTTPException(502, f"认证中心返回 {resp.status_code}")

    data = resp.json() or {}
    local = db.query(User).filter(User.email == username).first()
    return SSOIntrospectResponse(
        active=bool(data.get("active")),
        mfa_enabled=bool(data.get("mfa_enabled", False)),
        display_name=data.get("display_name"),
        local_email=local.email if local else None,
        sso_user_id=local.sso_user_id if local else None,
    )
