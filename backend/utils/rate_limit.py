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


class SlidingWindowLimiter:
    """滑动窗口限频器 — 在 window_seconds 内最多允许 max_attempts 次

    适用于登录等需要"N 次后限制"的场景。
    """

    def __init__(self, max_attempts: int = 5, window_seconds: int = 300, max_keys: int = 10000):
        self._max_attempts = max_attempts
        self._window = window_seconds
        self._max_keys = max_keys
        self._attempts: Dict[str, list] = {}  # key -> [timestamp, ...]
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        """检查是否允许，若允许则记录本次尝试"""
        now = time.monotonic()
        with self._lock:
            if len(self._attempts) >= self._max_keys:
                self._cleanup(now)

            timestamps = self._attempts.get(key, [])
            # 移除窗口外的旧记录
            timestamps = [t for t in timestamps if (now - t) < self._window]

            if len(timestamps) >= self._max_attempts:
                self._attempts[key] = timestamps
                return False

            timestamps.append(now)
            self._attempts[key] = timestamps
            return True

    def remaining(self, key: str) -> int:
        """剩余可用次数"""
        now = time.monotonic()
        with self._lock:
            timestamps = self._attempts.get(key, [])
            valid = [t for t in timestamps if (now - t) < self._window]
            return max(0, self._max_attempts - len(valid))

    def _cleanup(self, now: float):
        expired = [k for k, ts in self._attempts.items() if all((now - t) >= self._window for t in ts)]
        for k in expired:
            del self._attempts[k]

    def reset(self, key: str):
        with self._lock:
            self._attempts.pop(key, None)


# 全局实例：邮件通知限流器（每用户 5 分钟最多 1 封通知）
email_notification_limiter = MemoryRateLimiter(cooldown_seconds=300)

# 全局实例：邮件发送限流器（每用户约 10 封/分钟，即 6 秒冷却）
email_send_limiter = MemoryRateLimiter(cooldown_seconds=6)

# 全局实例：登录限频器（每 IP 5 分钟最多 10 次尝试）
login_limiter = SlidingWindowLimiter(max_attempts=10, window_seconds=300)
