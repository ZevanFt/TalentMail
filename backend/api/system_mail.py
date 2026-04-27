"""
系统邮件发送 API
提供模板邮件和原始邮件两种发送方式，通过 API Key + scope 鉴权。
供外部系统（如 AuthCenter）调用，发送验证邮件、通知等。

安全措施（纵深防御）:
  1. Caddy 层 IP 白名单（SYSTEM_API_ALLOWED_IPS 环境变量）
  2. FastAPI 层 IP 白名单（settings.SYSTEM_API_ALLOWED_IPS 配置项）
  3. API Key + scope 认证
"""
import ipaddress
import logging
import smtplib
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api import deps
from core.config import settings
from core.mail_service import MailService
from db.database import get_db
from db.models.system import ApiKey

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["System Email"])

# ---------- IP 白名单（纵深防御，Caddy 层已做第一道） ----------

_allowed_ips: set[str] | None = None


def _get_allowed_ips() -> set[str]:
    """解析配置中的 IP 白名单，懒加载 + 缓存。"""
    global _allowed_ips
    if _allowed_ips is not None:
        return _allowed_ips
    raw = settings.SYSTEM_API_ALLOWED_IPS.strip()
    if not raw:
        _allowed_ips = set()  # 空 = 不限制
        return _allowed_ips
    ips = set()
    for item in raw.replace(",", " ").split():
        item = item.strip()
        if item:
            ips.add(item)
    _allowed_ips = ips
    logger.info("系统 API IP 白名单已加载: %s", ips)
    return _allowed_ips


def _check_ip_whitelist(request: Request) -> None:
    """检查请求 IP 是否在白名单中。白名单为空时不限制。"""
    allowed = _get_allowed_ips()
    if not allowed:
        return  # 白名单未配置，不限制（Caddy 层兜底）
    client_ip = request.client.host if request.client else None
    if not client_ip:
        logger.warning("系统 API 请求缺少客户端 IP，拒绝访问")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    # 支持精确匹配和 CIDR 匹配
    for allowed_item in allowed:
        try:
            if "/" in allowed_item:
                if ipaddress.ip_address(client_ip) in ipaddress.ip_network(allowed_item, strict=False):
                    return
            elif client_ip == allowed_item:
                return
        except ValueError:
            continue
    logger.warning("系统 API 请求来自未授权 IP: %s", client_ip)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


# ---------- 请求模型 ----------

class SendTemplateRequest(BaseModel):
    """通过模板发送邮件的请求体"""
    to_email: str = Field(..., max_length=320, description="收件人邮箱")
    template_code: str = Field(..., max_length=100, description="模板代码")
    variables: Dict[str, str] = Field(default_factory=dict, description="模板变量")


class SendRawRequest(BaseModel):
    """直接发送邮件的请求体"""
    to_email: str = Field(..., max_length=320, description="收件人邮箱")
    subject: str = Field(..., max_length=998, description="邮件主题")
    body_html: str = Field(..., max_length=500_000, description="HTML 正文")
    body_text: Optional[str] = Field(default=None, max_length=200_000, description="纯文本正文")


# ---------- 端点 ----------

@router.post("/send-template")
def send_template_email(
    request: Request,
    payload: SendTemplateRequest,
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(deps.require_api_key_scopes(["system_email:send"])),
):
    """
    通过模板发送系统邮件。
    需要 API Key 且具有 system_email:send 权限。
    """
    _check_ip_whitelist(request)

    logger.info(
        "系统邮件发送请求(模板): to=%s, template=%s, api_key_id=%s, ip=%s",
        payload.to_email, payload.template_code, api_key.id,
        request.client.host if request.client else "unknown",
    )

    service = MailService(db)
    ok = service.send_by_template(
        template_code=payload.template_code,
        to_email=payload.to_email,
        context=payload.variables,
    )

    if not ok:
        logger.error(
            "系统邮件发送失败(模板): to=%s, template=%s",
            payload.to_email, payload.template_code,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="邮件发送失败，请稍后重试",
        )

    logger.info("系统邮件发送成功(模板): to=%s, template=%s", payload.to_email, payload.template_code)
    return {"status": "success", "message": f"邮件已发送至 {payload.to_email}"}


@router.post("/send-raw")
def send_raw_email(
    request: Request,
    payload: SendRawRequest,
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(deps.require_api_key_scopes(["system_email:send"])),
):
    """
    直接发送系统邮件（不使用模板）。
    需要 API Key 且具有 system_email:send 权限。
    """
    _check_ip_whitelist(request)

    logger.info(
        "系统邮件发送请求(原始): to=%s, subject=%s, api_key_id=%s, ip=%s",
        payload.to_email, payload.subject, api_key.id,
        request.client.host if request.client else "unknown",
    )

    service = MailService(db)
    ok = service.send_raw(
        to_email=payload.to_email,
        subject=payload.subject,
        body_html=payload.body_html,
        body_text=payload.body_text,
    )

    if not ok:
        logger.error(
            "系统邮件发送失败(原始): to=%s, subject=%s",
            payload.to_email, payload.subject,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="邮件发送失败，请稍后重试",
        )

    logger.info("系统邮件发送成功(原始): to=%s", payload.to_email)
    return {"status": "success", "message": f"邮件已发送至 {payload.to_email}"}


@router.get("/health")
def system_health(request: Request, db: Session = Depends(get_db)):
    """
    系统邮件服务健康检查（无需 API Key 认证）。
    检查 DB 连接和 SMTP 服务器可达性。
    供外部调用方（如 AuthCenter）探测邮件服务是否可用。
    """
    _check_ip_whitelist(request)

    checks = {"db": "unknown", "smtp": "unknown"}

    # 1. 数据库检查
    try:
        db.execute(text("SELECT 1"))
        checks["db"] = "connected"
    except Exception as exc:
        logger.error("系统邮件健康检查 — DB 连接失败: %s", exc)
        checks["db"] = "disconnected"

    # 2. SMTP 检查（仅建连 + NOOP，不发送邮件）
    try:
        with smtplib.SMTP(settings.MAIL_SERVER, settings.SMTP_PORT, timeout=5) as smtp_conn:
            smtp_conn.noop()
        checks["smtp"] = "reachable"
    except Exception as exc:
        logger.error("系统邮件健康检查 — SMTP 不可达: %s", exc)
        checks["smtp"] = "unreachable"

    all_ok = checks["db"] == "connected" and checks["smtp"] == "reachable"
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "ok" if all_ok else "degraded", **checks},
    )
