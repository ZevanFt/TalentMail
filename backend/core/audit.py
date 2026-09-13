"""平台操作审计写入与查询辅助"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from db.models.system import OperationAuditLog

logger = logging.getLogger(__name__)


def record_operation(
    db: Session,
    *,
    action: str,
    user_id: Optional[int] = None,
    actor_type: str = "user",
    resource_type: Optional[str] = None,
    resource_id: Optional[str | int] = None,
    detail: Optional[Any] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status: str = "success",
) -> None:
    """写入一条操作审计。失败只打日志，不影响主流程。"""
    try:
        detail_text: Optional[str] = None
        if detail is not None:
            if isinstance(detail, str):
                detail_text = detail[:2000]
            else:
                detail_text = json.dumps(detail, ensure_ascii=False, default=str)[:2000]

        db.add(
            OperationAuditLog(
                user_id=user_id,
                actor_type=actor_type,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id is not None else None,
                detail=detail_text,
                ip_address=ip_address,
                user_agent=(user_agent or None) and user_agent[:255],
                status=status,
            )
        )
        db.commit()
    except Exception as e:
        logger.error(f"[Audit] 写入操作审计失败 action={action}: {e}")
        try:
            db.rollback()
        except Exception:
            pass
