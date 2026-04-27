"""PGP 加密 API — 公钥管理与查找"""
import logging
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db.database import get_db
from api.deps import get_current_user
from db.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/encryption", tags=["Encryption"])

PGP_PUBLIC_KEY_PATTERN = re.compile(
    r'-----BEGIN PGP PUBLIC KEY BLOCK-----.*?-----END PGP PUBLIC KEY BLOCK-----',
    re.DOTALL,
)


class PublicKeyUpload(BaseModel):
    public_key: str
    fingerprint: Optional[str] = None


class PublicKeyResponse(BaseModel):
    has_key: bool
    fingerprint: Optional[str] = None
    created_at: Optional[datetime] = None
    public_key: Optional[str] = None


class PublicKeyLookup(BaseModel):
    email: str
    has_key: bool
    fingerprint: Optional[str] = None
    public_key: Optional[str] = None


@router.get("/my-key", response_model=PublicKeyResponse)
def get_my_key(user: User = Depends(get_current_user)):
    """获取自己的 PGP 公钥"""
    return PublicKeyResponse(
        has_key=bool(user.pgp_public_key),
        fingerprint=user.pgp_key_fingerprint,
        created_at=user.pgp_key_created_at,
        public_key=user.pgp_public_key,
    )


@router.post("/my-key", response_model=PublicKeyResponse)
def upload_my_key(
    data: PublicKeyUpload,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """上传/更新自己的 PGP 公钥"""
    key_text = data.public_key.strip()

    # 验证 PGP 公钥格式
    if not PGP_PUBLIC_KEY_PATTERN.match(key_text):
        raise HTTPException(400, "无效的 PGP 公钥格式（需要 ASCII Armor 格式）")

    # 限制大小（公钥不应超过 100KB）
    if len(key_text) > 100_000:
        raise HTTPException(400, "公钥过大（最大 100KB）")

    user.pgp_public_key = key_text
    user.pgp_key_fingerprint = data.fingerprint or _extract_simple_fingerprint(key_text)
    user.pgp_key_created_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    logger.info(f"用户 {user.id} 上传了 PGP 公钥 (fingerprint: {user.pgp_key_fingerprint})")

    return PublicKeyResponse(
        has_key=True,
        fingerprint=user.pgp_key_fingerprint,
        created_at=user.pgp_key_created_at,
        public_key=user.pgp_public_key,
    )


@router.delete("/my-key")
def delete_my_key(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """删除自己的 PGP 公钥"""
    user.pgp_public_key = None
    user.pgp_key_fingerprint = None
    user.pgp_key_created_at = None
    db.commit()
    logger.info(f"用户 {user.id} 删除了 PGP 公钥")
    return {"status": "success", "message": "公钥已删除"}


@router.get("/lookup", response_model=PublicKeyLookup)
def lookup_public_key(
    email: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),  # 需认证
):
    """查找平台用户的 PGP 公钥"""
    target = db.query(User).filter(User.email == email.strip().lower()).first()
    if not target or not target.pgp_public_key:
        return PublicKeyLookup(email=email, has_key=False)

    return PublicKeyLookup(
        email=email,
        has_key=True,
        fingerprint=target.pgp_key_fingerprint,
        public_key=target.pgp_public_key,
    )


def _extract_simple_fingerprint(key_text: str) -> str:
    """从 PGP 公钥中提取简单标识（前 16 字符的哈希）"""
    import hashlib
    # 取公钥内容部分的 SHA256 前 16 位作为简化指纹
    content = key_text.replace("-----BEGIN PGP PUBLIC KEY BLOCK-----", "") \
                      .replace("-----END PGP PUBLIC KEY BLOCK-----", "") \
                      .strip()
    return hashlib.sha256(content.encode()).hexdigest()[:16].upper()
