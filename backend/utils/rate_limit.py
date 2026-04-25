"""内存级别速率限制器

用于工作流通知防刷等场景。基于 TTL 的简单实现，无需外部依赖。
"""
import time
import threading
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class MemoryRateLimiter:
    """基于内存的 per-key 速率限制器

    每个 key（如 user_id + event_type）有独立的冷却窗口。
    线程安全，适用于单进程多协程/多线程场景。

    Usage:
        limiter = MemoryRateLimiter(cooldown_seconds=300)
        if limiter.allow("user:123:email.received"):
            # 允许操作
            ...
        else:
            # 被限流
            ...
    """

    def __init__(self, cooldown_seconds: int = 300, max_keys: int = 10000):
        """
        Args:
            cooldown_seconds: 同一 key 两次操作之间的最小间隔（秒）
            max_keys: 最大跟踪 key 数量，防止内存泄漏
        """
        self._cooldown = cooldown_seconds
        self._max_keys = max_keys
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        """检查给定 key 是否允许通过

        如果允许，同时更新该 key 的时间戳。
        """
        now = time.monotonic()
        with self._lock:
            last = self._timestamps.get(key)
            if last is not None and (now - last) < self._cooldown:
                return False

            # 清理过期条目（懒清理，每次允许时顺带清理）
            if len(self._timestamps) >= self._max_keys:
                self._cleanup(now)

            self._timestamps[key] = now
            return True

    def _cleanup(self, now: float):
        """清理已过期的条目"""
        expired_keys = [
            k for k, ts in self._timestamps.items()
            if (now - ts) >= self._cooldown
        ]
        for k in expired_keys:
            del self._timestamps[k]
        if expired_keys:
            logger.debug(f"[RateLimiter] 清理了 {len(expired_keys)} 个过期条目")

    def reset(self, key: str):
        """重置某个 key 的限流状态"""
        with self._lock:
            self._timestamps.pop(key, None)

    def clear_all(self):
        """清空所有限流状态"""
        with self._lock:
            self._timestamps.clear()


# 全局实例：邮件通知限流器（每用户 5 分钟最多 1 封通知）
email_notification_limiter = MemoryRateLimiter(cooldown_seconds=300)

# 全局实例：邮件发送限流器（每用户约 10 封/分钟，即 6 秒冷却）
email_send_limiter = MemoryRateLimiter(cooldown_seconds=6)
