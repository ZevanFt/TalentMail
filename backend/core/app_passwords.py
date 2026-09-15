"""应用专用密码：生成 / 校验 / 更新使用时间"""
from __future__ import annotations

import secrets
import string
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from core.security import get_password_hash, verify_password
from db.models.user import AppPassword

_ALPHABET = string.ascii_lowercase + string.digits
_PREFIX_LEN = 4
_BODY_LEN = 20
MAX_ACTIVE_PER_USER = 10


def generate_app_password() -> tuple[str, str, str]:
    """返回 (plaintext, prefix, password_hash)。明文形如 tm_abcd_efghijklmnopqrst_uvwxyz"""
    body = "".join(secrets.choice(_ALPHABET) for _ in range(_BODY_LEN))
    prefix = body[:_PREFIX_LEN]
    # 分组展示更易输入
    groups = [body[i : i + 4] for i in range(0, len(body), 4)]
    plaintext = "tm_" + "-".join(groups)
    return plaintext, prefix, get_password_hash(plaintext)


def verify_app_password(db: Session, user_id: int, plaintext: str) -> Optional[AppPassword]:
    """校验应用专用密码；成功则刷新 last_used_at 并返回记录。"""
    if not plaintext or not plaintext.startswith("tm_"):
        return None
    rows = (
        db.query(AppPassword)
        .filter(AppPassword.user_id == user_id, AppPassword.revoked_at.is_(None))
        .all()
    )
    for row in rows:
        try:
            if verify_password(plaintext, row.password_hash):
                row.last_used_at = datetime.now(timezone.utc)
                db.commit()
                return row
        except Exception:
            continue
    return None


def count_active(db: Session, user_id: int) -> int:
    return (
        db.query(AppPassword)
        .filter(AppPassword.user_id == user_id, AppPassword.revoked_at.is_(None))
        .count()
    )
