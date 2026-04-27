import hashlib
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.api_keys import extract_api_key_prefix, verify_api_key
from core import security
from crud import user as crud_user
from db import models
from db.database import get_db
from db.models.system import ApiKey, ApiKeyAuditLog

logger = logging.getLogger(__name__)

# ---------- API Key 验证缓存（减少 DB 查询） ----------
# key: SHA-256(raw_key) -> value: (api_key_id, expire_timestamp)
# 用 SHA-256(raw_key) 做缓存键，避免在内存中存储明文 API Key

_api_key_cache: Dict[str, Tuple[int, float]] = {}
_cache_lock = threading.Lock()
_CACHE_TTL = 60  # 60 秒缓存
_CACHE_MAX_SIZE = 1000  # 缓存上限，防止无限膨胀


def _cache_key(raw_key: str) -> str:
    """用 SHA-256 生成缓存键（不存储明文 key）。"""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _cache_get(cache_key: str) -> Optional[int]:
    """从缓存获取 api_key_id，过期则移除。"""
    with _cache_lock:
        entry = _api_key_cache.get(cache_key)
        if entry is not None:
            api_key_id, expires_at = entry
            if expires_at > time.time():
                return api_key_id
            # 过期，移除
            _api_key_cache.pop(cache_key, None)
    return None


def _cache_set(cache_key: str, api_key_id: int) -> None:
    """写入缓存。超过上限时清理过期条目。"""
    now = time.time()
    with _cache_lock:
        # 缓存接近上限时，清理过期条目
        if len(_api_key_cache) >= _CACHE_MAX_SIZE:
            expired_keys = [k for k, (_, exp) in _api_key_cache.items() if exp <= now]
            for k in expired_keys:
                _api_key_cache.pop(k, None)
            # 如果清理后仍满，放弃写入（不阻塞请求）
            if len(_api_key_cache) >= _CACHE_MAX_SIZE:
                return
        _api_key_cache[cache_key] = (api_key_id, now + _CACHE_TTL)


def get_current_user(
    token: str = Depends(security.oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    """
    Dependency to get the current user from a token.
    验证 JWT + 检查会话是否仍然有效（未被撤销）。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = security.verify_token(token)
    if not token_data:
        raise credentials_exception

    # 检查会话是否已被撤销（如果 token 中包含 session_id）
    if token_data.session_id:
        session = db.query(models.UserSession).filter(
            models.UserSession.id == token_data.session_id,
            models.UserSession.is_active == True,  # noqa: E712
        ).first()
        if not session:
            raise credentials_exception

    user = crud_user.get_user_by_email(db, email=token_data.sub)
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Dependency to get the current active user.
    注：User 模型目前没有 is_active 字段（只有 UserSession 有）。
    如果未来 User 加了 is_active 字段，在此处启用检查。
    """
    return current_user


def get_current_user_from_token(db: Session, token: str) -> models.User | None:
    """从 token 获取用户（用于 WebSocket 认证）"""
    token_data = security.verify_token(token)
    if not token_data:
        return None
    return crud_user.get_user_by_email(db, email=token_data.sub)


def get_current_admin_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Dependency to get the current admin user.
    Raises 403 if user is not an admin.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


def get_current_session_id(
    token: str = Depends(security.oauth2_scheme)
) -> Optional[int]:
    """
    从 token 中获取当前会话 ID
    """
    token_data = security.verify_token(token)
    if not token_data:
        return None

    # 从 token_data 中获取 session_id
    return getattr(token_data, 'session_id', None)


api_key_scheme = HTTPBearer(auto_error=False)


def get_current_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(api_key_scheme),
    db: Session = Depends(get_db),
) -> ApiKey:
    """通过 Bearer API Key 认证，返回当前有效密钥记录。"""
    request_ip = request.client.host if request.client else None
    request_path = request.url.path if request.url else None
    request_method = request.method if request.method else None

    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raw_key = credentials.credentials.strip()

    # 尝试从缓存获取 api_key_id（跳过 prefix 查询 + hash 遍历）
    ck = _cache_key(raw_key)
    cached_id = _cache_get(ck)

    if cached_id is not None:
        matched_key = db.query(ApiKey).get(cached_id)
        if matched_key is None:
            # 缓存的 key 已被删除，清除缓存走正常流程
            with _cache_lock:
                _api_key_cache.pop(ck, None)
            cached_id = None

    if cached_id is None:
        # 缓存未命中，走完整的 prefix 查询 + hash 验证
        key_prefix = extract_api_key_prefix(raw_key)
        candidates = (
            db.query(ApiKey)
            .filter(ApiKey.key_prefix == key_prefix)
            .all()
        )
        if not candidates:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        matched_key = None
        for candidate in candidates:
            if verify_api_key(raw_key, candidate.key_hash):
                matched_key = candidate
                break

        if matched_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 验证通过，写入缓存
        _cache_set(ck, matched_key.id)

    now = datetime.now(timezone.utc)
    if matched_key.revoked_at is not None:
        db.add(
            ApiKeyAuditLog(
                api_key_id=matched_key.id,
                user_id=matched_key.user_id,
                method=request_method,
                path=request_path,
                ip_address=request_ip,
                status_code=status.HTTP_401_UNAUTHORIZED,
                decision="deny",
                error_code="revoked",
            )
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if matched_key.expires_at is not None and matched_key.expires_at <= now:
        db.add(
            ApiKeyAuditLog(
                api_key_id=matched_key.id,
                user_id=matched_key.user_id,
                method=request_method,
                path=request_path,
                ip_address=request_ip,
                status_code=status.HTTP_401_UNAUTHORIZED,
                decision="deny",
                error_code="expired",
            )
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    window_start = now.replace(second=0, microsecond=0)
    used_count = db.query(ApiKeyAuditLog).filter(
        ApiKeyAuditLog.api_key_id == matched_key.id,
        ApiKeyAuditLog.created_at >= window_start,
    ).count()
    if used_count >= matched_key.rate_limit_per_minute:
        db.add(
            ApiKeyAuditLog(
                api_key_id=matched_key.id,
                user_id=matched_key.user_id,
                method=request_method,
                path=request_path,
                ip_address=request_ip,
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                decision="deny",
                error_code="rate_limited",
            )
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="API key rate limit exceeded",
        )

    matched_key.last_used_at = now
    db.add(
        ApiKeyAuditLog(
            api_key_id=matched_key.id,
            user_id=matched_key.user_id,
            method=request_method,
            path=request_path,
            ip_address=request_ip,
            status_code=status.HTTP_200_OK,
            decision="allow",
            error_code=None,
        )
    )
    return matched_key


def get_api_key_user(api_key: ApiKey = Depends(get_current_api_key)) -> models.User:
    """返回 API Key 所属用户。"""
    return api_key.user


def require_api_key_scopes(required_scopes: List[str]):
    """生成 scope 校验依赖，要求 API Key 拥有全部 required_scopes。"""
    def _dependency(api_key: ApiKey = Depends(get_current_api_key)) -> ApiKey:
        current_scopes = set(api_key.scopes or [])
        missing_scopes = [scope for scope in required_scopes if scope not in current_scopes]
        if missing_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing scopes: {', '.join(missing_scopes)}",
            )
        return api_key

    return _dependency
