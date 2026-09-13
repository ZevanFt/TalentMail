"""
健康检查 API
用于容器健康检查和负载均衡器探测
"""
import logging
import os
import shutil
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

_PROCESS_START = time.time()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    健康检查端点

    检查项：
    1. API 服务是否运行
    2. 数据库连接是否正常
    3. 后台任务存活状态
    4. 上传目录可写 / 磁盘余量
    5. 可选：mailserver 容器探测（由运维侧聚合）

    Returns:
        200 healthy / degraded / 503 unhealthy
    """
    checks: dict = {}
    db_ok = True

    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        db_ok = False
        checks["database"] = "disconnected"
        logger.error(f"[Health] 数据库连接失败: {e}")

    # 后台任务
    try:
        from main import get_task_status
        tasks = get_task_status()
        dead_tasks = [n for n, s in tasks.items() if not s["running"]]
        checks["background_tasks"] = tasks
        if dead_tasks:
            checks["dead_tasks"] = dead_tasks
    except Exception as e:
        logger.error(f"[Health] 获取后台任务状态失败: {e}")
        checks["background_tasks"] = {}
        dead_tasks = ["unknown"]
        checks["dead_tasks"] = dead_tasks

    # 磁盘 / 上传目录
    upload_dir = os.getenv("UPLOAD_DIR", "/app/backend/uploads")
    disk_info = {"path": upload_dir, "exists": False}
    try:
        os.makedirs(upload_dir, exist_ok=True)
        disk_info["exists"] = True
        usage = shutil.disk_usage(upload_dir)
        disk_info["total_bytes"] = usage.total
        disk_info["free_bytes"] = usage.free
        disk_info["used_percent"] = round((usage.used / usage.total) * 100, 1) if usage.total else None
        if usage.free < 100 * 1024 * 1024:  # <100MB
            disk_info["warning"] = "磁盘剩余空间不足 100MB"
    except Exception as e:
        disk_info["error"] = str(e)
    checks["disk"] = disk_info

    # 邮件队列（可选，探测失败不影响健康判定）
    try:
        from core.alerting import get_mail_queue_depth
        queue_depth = get_mail_queue_depth()
        checks["mail_queue"] = {"depth": queue_depth}
        if queue_depth is not None:
            from core.config import settings as _s
            threshold = getattr(_s, "MAIL_QUEUE_WARN_THRESHOLD", 50)
            if queue_depth >= threshold:
                checks["mail_queue"]["warning"] = f"队列积压 {queue_depth}（阈值 {threshold}）"
    except Exception as e:
        checks["mail_queue"] = {"depth": None, "error": str(e)}

    # 运行时长
    uptime = round(time.time() - _PROCESS_START, 1)
    checks["uptime_seconds"] = uptime
    checks["timestamp"] = datetime.now(timezone.utc).isoformat()

    if not db_ok:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "service": "talentmail-backend", **checks})

    degraded = bool(checks.get("dead_tasks")) or bool(checks.get("mail_queue", {}).get("warning"))
    overall = "degraded" if degraded else "healthy"
    return {"status": overall, "service": "talentmail-backend", **checks}


@router.get("/readiness")
async def readiness_check(db: Session = Depends(get_db)):
    """
    就绪检查端点

    检查服务是否准备好接收流量

    Returns:
        200 ready / 503 not_ready
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "service": "talentmail-backend"}
    except Exception as e:
        logger.error(f"[Readiness] 数据库连接失败: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "service": "talentmail-backend"},
        )


@router.get("/liveness")
async def liveness_check():
    """
    存活检查端点

    检查服务进程是否存活

    Returns:
        dict: 存活状态信息
    """
    return {
        "status": "alive",
        "service": "talentmail-backend",
        "uptime_seconds": round(time.time() - _PROCESS_START, 1),
    }
