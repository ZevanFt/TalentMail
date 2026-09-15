"""进程内性能指标：API 延迟、mail_sync 耗时、慢查询计数。

仅内存环形缓冲，不落库；供 /api/health 与 periodic_health_monitor 读取。
"""
from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional

_lock = threading.Lock()

# API 延迟（秒），保留最近 N 条
_API_LATENCY: Deque[float] = deque(maxlen=500)
_API_TOTAL = 0
_API_4XX = 0
_API_5XX = 0

# mail_sync
_MAIL_SYNC: Dict[str, Any] = {
    "last_duration_sec": None,
    "last_finished_at": None,
    "last_total_new": None,
    "last_error": None,
    "avg_duration_sec": None,
    "_recent": deque(maxlen=30),  # 最近耗时
}

# 慢查询
_SLOW_QUERY_THRESHOLD_MS = 500.0
_SLOW_QUERIES: Deque[Dict[str, Any]] = deque(maxlen=50)
_SLOW_QUERY_COUNT = 0
_SQL_HOOK_INSTALLED = False


def record_api_latency(seconds: float, status_code: int) -> None:
    global _API_TOTAL, _API_4XX, _API_5XX
    with _lock:
        _API_LATENCY.append(max(0.0, seconds))
        _API_TOTAL += 1
        if status_code >= 500:
            _API_5XX += 1
        elif status_code >= 400:
            _API_4XX += 1


def record_mail_sync(duration_sec: float, total_new: int = 0, error: Optional[str] = None) -> None:
    with _lock:
        _MAIL_SYNC["last_duration_sec"] = round(duration_sec, 3)
        _MAIL_SYNC["last_finished_at"] = time.time()
        _MAIL_SYNC["last_total_new"] = total_new
        _MAIL_SYNC["last_error"] = error
        if error is None:
            _MAIL_SYNC["_recent"].append(duration_sec)
            recent = list(_MAIL_SYNC["_recent"])
            _MAIL_SYNC["avg_duration_sec"] = round(sum(recent) / len(recent), 3) if recent else None


def record_slow_query(duration_ms: float, statement: str) -> None:
    global _SLOW_QUERY_COUNT
    snippet = (statement or "").strip().replace("\n", " ")[:200]
    with _lock:
        _SLOW_QUERY_COUNT += 1
        _SLOW_QUERIES.append({
            "duration_ms": round(duration_ms, 1),
            "statement": snippet,
            "at": time.time(),
        })


def set_slow_query_threshold(ms: float) -> None:
    global _SLOW_QUERY_THRESHOLD_MS
    _SLOW_QUERY_THRESHOLD_MS = max(1.0, float(ms))


def install_sql_slow_query_hook(engine) -> None:
    """挂 SQLAlchemy 事件钩子，统计超过阈值的查询。幂等。"""
    global _SQL_HOOK_INSTALLED
    if _SQL_HOOK_INSTALLED:
        return
    try:
        from sqlalchemy import event
        from sqlalchemy.engine import Engine
    except Exception:
        return

    # 每个连接记录起始时间（thread-local 风格：用连接 info 字典）
    @event.listens_for(engine, "before_cursor_execute")
    def _before(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
        conn.info["query_start"] = time.perf_counter()

    @event.listens_for(engine, "after_cursor_execute")
    def _after(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
        start = conn.info.pop("query_start", None)
        if start is None:
            return
        ms = (time.perf_counter() - start) * 1000.0
        if ms >= _SLOW_QUERY_THRESHOLD_MS:
            record_slow_query(ms, statement)

    _SQL_HOOK_INSTALLED = True


def _percentile(sorted_vals: List[float], p: float) -> Optional[float]:
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    idx = min(len(sorted_vals) - 1, max(0, int(round((p / 100.0) * (len(sorted_vals) - 1)))))
    return sorted_vals[idx]


def get_metrics_snapshot() -> Dict[str, Any]:
    with _lock:
        lat = sorted(_API_LATENCY)
        api = {
            "samples": len(lat),
            "total_requests": _API_TOTAL,
            "errors_4xx": _API_4XX,
            "errors_5xx": _API_5XX,
            "p50_ms": round(_percentile(lat, 50) * 1000, 1) if lat else None,
            "p95_ms": round(_percentile(lat, 95) * 1000, 1) if lat else None,
            "p99_ms": round(_percentile(lat, 99) * 1000, 1) if lat else None,
            "avg_ms": round((sum(lat) / len(lat)) * 1000, 1) if lat else None,
            "max_ms": round(lat[-1] * 1000, 1) if lat else None,
        }
        mail_sync = {
            "last_duration_sec": _MAIL_SYNC["last_duration_sec"],
            "avg_duration_sec": _MAIL_SYNC["avg_duration_sec"],
            "last_finished_at": _MAIL_SYNC["last_finished_at"],
            "last_total_new": _MAIL_SYNC["last_total_new"],
            "last_error": _MAIL_SYNC["last_error"],
        }
        slow = {
            "threshold_ms": _SLOW_QUERY_THRESHOLD_MS,
            "count": _SLOW_QUERY_COUNT,
            "recent": list(_SLOW_QUERIES)[-5:],
        }
    return {"api": api, "mail_sync": mail_sync, "slow_queries": slow}
