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

    # 性能指标：API 延迟 / mail_sync / 慢查询
    try:
        from core import metrics as perf_metrics
        from core.config import settings as _settings
        perf = perf_metrics.get_metrics_snapshot()
        checks["performance"] = perf
        p95_warn = getattr(_settings, "API_LATENCY_P95_WARN_MS", 2000.0)
        p95 = perf.get("api", {}).get("p95_ms")
        if p95 is not None and p95 >= p95_warn:
            checks.setdefault("performance", {}).setdefault("api", {})["warning"] = (
                f"P95 {p95:.0f}ms 超过阈值 {p95_warn:.0f}ms"
            )
        ms_dur = perf.get("mail_sync", {}).get("last_duration_sec")
        ms_warn = getattr(_settings, "MAIL_SYNC_WARN_SECONDS", 90.0)
        if ms_dur is not None and ms_dur >= ms_warn:
            checks["performance"]["mail_sync"]["warning"] = (
                f"最近同步耗时 {ms_dur:.1f}s 超过阈值 {ms_warn:.0f}s"
            )
        if perf.get("mail_sync", {}).get("last_error"):
            checks["performance"]["mail_sync"]["warning"] = (
                f"最近同步失败: {perf['mail_sync']['last_error'][:120]}"
            )
        slow_count = perf.get("slow_queries", {}).get("count", 0)
        slow_warn_n = getattr(_settings, "SLOW_QUERY_WARN_COUNT", 30)
        if slow_count >= slow_warn_n:
            checks["performance"]["slow_queries"]["warning"] = (
                f"累计慢查询 {slow_count} 条（阈值 {slow_warn_n}）"
            )
    except Exception as e:
        logger.error(f"[Health] 获取性能指标失败: {e}")
        checks["performance"] = {"error": str(e)}

    # 运行时长
    uptime = round(time.time() - _PROCESS_START, 1)
    checks["uptime_seconds"] = uptime
    checks["timestamp"] = datetime.now(timezone.utc).isoformat()

    if not db_ok:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "service": "talentmail-backend", **checks})

    perf_warn = False
    perf_block = checks.get("performance") or {}
    if isinstance(perf_block, dict):
        perf_warn = any(
            isinstance(v, dict) and v.get("warning")
            for v in (perf_block.get("api"), perf_block.get("mail_sync"), perf_block.get("slow_queries"))
        )
    degraded = (
        bool(checks.get("dead_tasks"))
        or bool(checks.get("mail_queue", {}).get("warning"))
        or perf_warn
    )
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
