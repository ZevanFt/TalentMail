"""管理端运维 API：操作审计查询、备份列表/触发、系统概览"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_current_admin_user
from core.audit import record_operation
from db import models
from db.database import get_db
from db.models.system import OperationAuditLog
from utils.rate_limit import SlidingWindowLimiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin Ops"])

_backup_limiter = SlidingWindowLimiter(max_attempts=3, window_seconds=300)

# 备份目录与脚本路径（可通过环境变量覆盖）
BACKUP_DIR = Path(os.getenv("TALENTMAIL_BACKUP_DIR", "/var/backups/talentmail"))
BACKUP_SCRIPT = Path(os.getenv("TALENTMAIL_BACKUP_SCRIPT", "/app/scripts/backup-db.sh"))
PROJECT_ROOT = Path(os.getenv("TALENTMAIL_PROJECT_ROOT", "/app"))


class OperationAuditItem(BaseModel):
    id: int
    user_id: Optional[int]
    actor_type: str
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    detail: Optional[str]
    ip_address: Optional[str]
    status: str
    created_at: datetime


class OperationAuditListResponse(BaseModel):
    items: List[OperationAuditItem]
    total: int


class BackupFileItem(BaseModel):
    name: str
    size_bytes: int
    modified_at: datetime


class BackupListResponse(BaseModel):
    directory: str
    items: List[BackupFileItem]
    keep_count: int


class BackupTriggerResponse(BaseModel):
    status: str
    message: str
    duration_seconds: float
    newest_file: Optional[str] = None


@router.get("/audit/operations", response_model=OperationAuditListResponse)
def list_operation_audits(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = Query(None, max_length=64),
    user_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None, max_length=16),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin_user),
):
    query = db.query(OperationAuditLog)

    if action:
        query = query.filter(OperationAuditLog.action == action)
    if user_id is not None:
        query = query.filter(OperationAuditLog.user_id == user_id)
    if status:
        query = query.filter(OperationAuditLog.status == status)

    total = query.count()
    rows = (
        query.order_by(OperationAuditLog.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return OperationAuditListResponse(
        items=[
            OperationAuditItem(
                id=r.id,
                user_id=r.user_id,
                actor_type=r.actor_type,
                action=r.action,
                resource_type=r.resource_type,
                resource_id=r.resource_id,
                detail=r.detail,
                ip_address=r.ip_address,
                status=r.status,
                created_at=r.created_at,
            )
            for r in rows
        ],
        total=total,
    )


@router.get("/backups", response_model=BackupListResponse)
def list_backups(
    _: models.User = Depends(get_current_admin_user),
):
    keep = int(os.getenv("TALENTMAIL_BACKUP_KEEP", "7"))
    items: List[BackupFileItem] = []
    if BACKUP_DIR.exists():
        patterns = (
            "talentmail-*.sql.gz",
            "talentmail-*.sql.gz.enc",
            "talentmail-uploads-*.tar.gz",
            "talentmail-uploads-*.tar.gz.enc",
        )
        seen = set()
        paths = []
        for pattern in patterns:
            for path in BACKUP_DIR.glob(pattern):
                if path.name not in seen:
                    seen.add(path.name)
                    paths.append(path)
        for path in sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True):
            st = path.stat()
            items.append(
                BackupFileItem(
                    name=path.name,
                    size_bytes=st.st_size,
                    modified_at=datetime.fromtimestamp(st.st_mtime, tz=timezone.utc),
                )
            )
    return BackupListResponse(directory=str(BACKUP_DIR), items=items, keep_count=keep)


def _resolve_backup_script() -> Path:
    candidates = [
        BACKUP_SCRIPT,
        PROJECT_ROOT / "scripts" / "backup-db.sh",
        Path(__file__).resolve().parents[2] / "scripts" / "backup-db.sh",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise HTTPException(500, "备份脚本不存在，请检查 TALENTMAIL_BACKUP_SCRIPT 配置")


@router.post("/backups/trigger", response_model=BackupTriggerResponse)
def trigger_backup(
    request: Request,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin_user),
):
    if not _backup_limiter.allow(f"backup:{admin.id}"):
        raise HTTPException(429, "备份触发过于频繁，请稍后再试")

    script = _resolve_backup_script()
    if shutil.which("bash") is None and os.name != "nt":
        # 容器内应有 bash；Windows 本地开发直接返回提示
        raise HTTPException(500, "当前环境缺少 bash，无法执行备份脚本")

    started = time.monotonic()
    try:
        result = subprocess.run(
            ["bash", str(script)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ},
        )
    except subprocess.TimeoutExpired:
        record_operation(
            db,
            action="backup.create",
            user_id=admin.id,
            actor_type="admin",
            resource_type="backup",
            status="failure",
            detail={"error": "timeout"},
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(504, "备份执行超时")

    duration = round(time.monotonic() - started, 2)
    if result.returncode != 0:
        record_operation(
            db,
            action="backup.create",
            user_id=admin.id,
            actor_type="admin",
            resource_type="backup",
            status="failure",
            detail={"exit_code": result.returncode, "stderr": (result.stderr or "")[-500:]},
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(500, f"备份失败: {(result.stderr or result.stdout or '').strip()[:300]}")

    newest = None
    if BACKUP_DIR.exists():
        files = sorted(BACKUP_DIR.glob("talentmail-*.sql.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
        if files:
            newest = files[0].name

    record_operation(
        db,
        action="backup.create",
        user_id=admin.id,
        actor_type="admin",
        resource_type="backup",
        resource_id=newest,
        status="success",
        detail={"duration_seconds": duration},
        ip_address=request.client.host if request.client else None,
    )
    return BackupTriggerResponse(
        status="success",
        message="备份完成",
        duration_seconds=duration,
        newest_file=newest,
    )
