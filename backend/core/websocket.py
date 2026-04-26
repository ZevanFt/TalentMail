"""WebSocket 连接管理，用于实时推送新邮件通知"""
from fastapi import WebSocket
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)

# 存储每个用户的 WebSocket 连接（列表保序，尾部最新）
# key: user_id, value: list of WebSocket connections (oldest first)
connections: Dict[int, List[WebSocket]] = {}

# 每用户最大同时连接数（防止 DoS）
MAX_CONNECTIONS_PER_USER = 5


async def connect(websocket: WebSocket, user_id: int):
    """添加用户连接（超过上限时关闭最早的连接）"""
    await websocket.accept()
    if user_id not in connections:
        connections[user_id] = []

    # 超过上限时驱逐最旧的连接（列表头部 = 最早）
    while len(connections[user_id]) >= MAX_CONNECTIONS_PER_USER:
        oldest = connections[user_id].pop(0)
        try:
            await oldest.close(code=4002, reason="Too many connections")
        except Exception:
            pass
        logger.info(f"WebSocket 驱逐最旧连接: user_id={user_id}")

    connections[user_id].append(websocket)
    logger.info(f"WebSocket 连接: user_id={user_id}, 当前连接数={len(connections[user_id])}")


def disconnect(websocket: WebSocket, user_id: int):
    """移除用户连接"""
    if user_id in connections:
        try:
            connections[user_id].remove(websocket)
        except ValueError:
            pass
        if not connections[user_id]:
            del connections[user_id]
    logger.info(f"WebSocket 断开: user_id={user_id}")


async def notify_new_email(user_id: int, email_data: dict = None):
    """通知用户有新邮件"""
    if user_id not in connections:
        return

    message = json.dumps({
        "type": "new_email",
        "data": email_data or {}
    })

    dead_connections = []
    for ws in connections[user_id]:
        try:
            await ws.send_text(message)
        except Exception:
            dead_connections.append(ws)

    # 清理断开的连接
    if dead_connections:
        for ws in dead_connections:
            try:
                connections[user_id].remove(ws)
            except ValueError:
                pass
        logger.debug(f"清理 {len(dead_connections)} 个死连接: user_id={user_id}")


async def broadcast_to_user(user_id: int, message_type: str, data: dict = None):
    """向用户广播消息"""
    if user_id not in connections:
        return

    message = json.dumps({
        "type": message_type,
        "data": data or {}
    })

    dead_connections = []
    for ws in connections[user_id]:
        try:
            await ws.send_text(message)
        except Exception:
            dead_connections.append(ws)

    if dead_connections:
        for ws in dead_connections:
            try:
                connections[user_id].remove(ws)
            except ValueError:
                pass
        logger.debug(f"清理 {len(dead_connections)} 个死连接: user_id={user_id}")
