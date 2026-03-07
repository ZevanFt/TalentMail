import hashlib
import hmac
import secrets
from typing import Tuple

from core.config import settings


def hash_api_key(raw_key: str) -> str:
    """计算 API Key 的 SHA-256 哈希值。"""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """以常量时间比较 API Key 哈希。"""
    computed_hash = hash_api_key(raw_key)
    return hmac.compare_digest(computed_hash, stored_hash)


def extract_api_key_prefix(raw_key: str) -> str:
    """提取 API Key 前缀，用于快速索引查询。"""
    return raw_key[: settings.API_KEY_PREFIX_LENGTH]


def generate_api_key() -> Tuple[str, str, str]:
    """
    生成 API Key。

    Returns:
        (raw_key, key_prefix, key_hash)
    """
    token = secrets.token_urlsafe(32)
    raw_key = f"{settings.API_KEY_TOKEN_PREFIX}{token}"
    key_prefix = extract_api_key_prefix(raw_key)
    key_hash = hash_api_key(raw_key)
    return raw_key, key_prefix, key_hash
