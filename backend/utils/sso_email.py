"""SSO 邮箱规范化与匹配候选规则"""
from __future__ import annotations

from typing import List, Optional, Union


def normalize_sso_email(
    sso_username: Optional[str],
    sso_user_id: Union[str, int],
    base_domain: str,
) -> str:
    """把 auth-center 用户名规范成本地邮箱。

    - 完整邮箱原样保留
    - 纯用户名补 `@base_domain`
    - 为空时回退到 `sso_{user_id}@base_domain`
    """
    email_local = (sso_username or "").strip()
    if email_local and "@" not in email_local:
        email_local = f"{email_local}@{base_domain}"
    if not email_local:
        email_local = f"sso_{sso_user_id}@{base_domain}"
    return email_local


def email_match_candidates(sso_username: Optional[str], base_domain: str) -> List[str]:
    """关联已有用户时的邮箱候选（兼容纯用户名与完整邮箱）。"""
    candidates: List[str] = []
    if sso_username:
        raw = sso_username.strip()
        if raw:
            candidates.append(raw)
            if "@" not in raw:
                candidates.append(f"{raw}@{base_domain}")
    return list(dict.fromkeys(candidates))
