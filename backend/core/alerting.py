"""运维告警与邮件队列探测"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import httpx

from core.config import settings

logger = logging.getLogger(__name__)

# 告警冷却：alert_key -> last_sent_ts
_alert_cooldown: Dict[str, float] = {}


def get_mail_queue_depth() -> Optional[int]:
    """探测 mailserver 容器内 Postfix 队列深度。失败返回 None。"""
    try:
        from core.mailserver_sync import get_docker_client, MAILSERVER_CONTAINER_NAME
        client = get_docker_client()
        if client is None:
            return None
        container = client.containers.get(MAILSERVER_CONTAINER_NAME)
        # postqueue -p 输出末行类似 "Mail queue is empty" 或多行邮件
        result = container.exec_run(["postqueue", "-p"], demux=True)
        if result.exit_code != 0:
            return None
        stdout = result.output[0].decode("utf-8", errors="replace") if result.output and result.output[0] else ""
        if "empty" in stdout.lower():
            return 0
        # 统计队列条目：以 "-- " 开头的分隔行数量，或按空行分段
        lines = [ln for ln in stdout.splitlines() if ln.strip()]
        # Postfix 多队列输出每条邮件以 "-- " 分隔
        separators = sum(1 for ln in lines if ln.startswith("--"))
        if separators > 0:
            return separators
        # 退化：有内容但无法解析时，粗略用非空行/3
        return max(0, len(lines) // 3) if lines else 0
    except Exception as e:
        logger.debug(f"[Alert] 邮件队列探测失败: {e}")
        return None


def should_send_alert(alert_key: str) -> bool:
    cooldown = max(60, int(settings.ALERT_COOLDOWN_SECONDS or 1800))
    now = time.time()
    last = _alert_cooldown.get(alert_key)
    if last is not None and (now - last) < cooldown:
        return False
    _alert_cooldown[alert_key] = now
    return True


def send_webhook_alert(
    title: str,
    message: str,
    *,
    level: str = "warning",
    extra: Optional[Dict[str, Any]] = None,
    alert_key: Optional[str] = None,
) -> bool:
    """发送告警到 Webhook。未配置 URL 时直接返回 False。"""
    url = (settings.ALERT_WEBHOOK_URL or "").strip()
    if not url:
        return False

    key = alert_key or title
    if not should_send_alert(key):
        return False

    payload = {
        "title": title,
        "message": message,
        "level": level,
        "service": "talentmail-backend",
        "timestamp": time.time(),
        **(extra or {}),
    }
    try:
        resp = httpx.post(url, json=payload, timeout=5.0)
        if resp.status_code >= 400:
            logger.error(f"[Alert] Webhook 返回 {resp.status_code}: {resp.text[:200]}")
            return False
        logger.info(f"[Alert] 已发送告警: {title}")
        return True
    except Exception as e:
        logger.error(f"[Alert] Webhook 发送失败: {e}")
        return False
