"""
事件发布器 - 统一管理系统事件的发布和处理
用于触发自动化规则引擎
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EventType:
    """系统事件类型常量"""
    
    # ========== 用户事件 ==========
    USER_REGISTERED = "user.registered"           # 用户注册成功
    USER_LOGIN = "user.login"                     # 用户登录
    USER_LOGIN_NEW_DEVICE = "user.login_new_device"  # 新设备登录
    USER_PASSWORD_CHANGED = "user.password_changed"  # 密码修改
    USER_PROFILE_UPDATED = "user.profile_updated"    # 资料更新
    USER_SUBSCRIPTION_CHANGED = "user.subscription_changed"  # 订阅变更
    
    # ========== 邮件事件 ==========
    EMAIL_RECEIVED = "email.received"             # 收到新邮件
    EMAIL_SENT = "email.sent"                     # 邮件发送成功
    EMAIL_BOUNCED = "email.bounced"               # 邮件退信
    EMAIL_OPENED = "email.opened"                 # 邮件被打开（追踪）
    EMAIL_LINK_CLICKED = "email.link_clicked"     # 邮件链接被点击
    
    # ========== 文件事件 ==========
    FILE_UPLOADED = "drive.file_uploaded"         # 文件上传
    FILE_SHARED = "drive.file_shared"             # 文件分享
    FILE_DOWNLOADED = "drive.file_downloaded"     # 文件下载
    
    # ========== 管理事件 ==========
    INVITE_CREATED = "admin.invite_created"       # 创建邀请码
    INVITE_USED = "admin.invite_used"             # 邀请码被使用
    USER_CREATED_BY_ADMIN = "admin.user_created"  # 管理员创建用户
    
    # ========== 系统事件 ==========
    STORAGE_LIMIT_WARNING = "system.storage_limit_warning"  # 存储空间警告
    SUBSCRIPTION_EXPIRING = "system.subscription_expiring"  # 订阅即将到期


# 事件类型元数据（用于前端显示）
EVENT_METADATA = {
    EventType.USER_REGISTERED: {
        "name": "用户注册成功",
        "category": "user",
        "category_label": "👤 用户事件",
        "description": "当新用户完成注册后触发",
        "available_variables": ["user_name", "user_email", "register_time", "login_url"]
    },
    EventType.USER_LOGIN: {
        "name": "用户登录",
        "category": "user",
        "category_label": "👤 用户事件",
        "description": "当用户登录时触发",
        "available_variables": ["user_name", "user_email", "login_time", "login_ip", "login_device"]
    },
    EventType.USER_LOGIN_NEW_DEVICE: {
        "name": "新设备登录",
        "category": "user",
        "category_label": "👤 用户事件",
        "description": "当用户从新设备登录时触发",
        "available_variables": ["user_name", "user_email", "login_time", "login_ip", "login_device", "login_location"]
    },
    EventType.USER_PASSWORD_CHANGED: {
        "name": "密码修改成功",
        "category": "user",
        "category_label": "👤 用户事件",
        "description": "当用户修改密码后触发",
        "available_variables": ["user_name", "user_email", "change_time"]
    },
    EventType.EMAIL_RECEIVED: {
        "name": "收到新邮件",
        "category": "email",
        "category_label": "📧 邮件事件",
        "description": "当收到新邮件时触发",
        "available_variables": ["sender_email", "sender_name", "subject", "received_time"]
    },
    EventType.EMAIL_SENT: {
        "name": "邮件发送成功",
        "category": "email",
        "category_label": "📧 邮件事件",
        "description": "当邮件发送成功后触发",
        "available_variables": ["recipient_email", "subject", "sent_time"]
    },
    EventType.FILE_SHARED: {
        "name": "文件被分享",
        "category": "drive",
        "category_label": "📁 文件事件",
        "description": "当用户分享文件时触发",
        "available_variables": ["sender_name", "sender_email", "file_name", "file_size", "share_url", "expires_at"]
    },
    EventType.INVITE_CREATED: {
        "name": "创建邀请码",
        "category": "admin",
        "category_label": "🔧 管理事件",
        "description": "当管理员创建邀请码时触发",
        "available_variables": ["inviter_name", "inviter_email", "invite_code", "invite_url", "expires_at"]
    },
    EventType.STORAGE_LIMIT_WARNING: {
        "name": "存储空间警告",
        "category": "system",
        "category_label": "⚙️ 系统事件",
        "description": "当用户存储空间使用超过阈值时触发",
        "available_variables": ["user_name", "user_email", "used_percent", "used_size", "total_size"]
    },
}


class EventPublisher:
    """
    事件发布器
    负责发布系统事件并触发相关的自动化规则
    """
    
    @classmethod
    async def publish(
        cls,
        event_type: str,
        data: Dict[str, Any],
        user = None,
        db: Session = None
    ) -> List[Any]:
        """
        发布事件，触发相关的自动化规则
        
        Args:
            event_type: 事件类型（使用 EventType 常量）
            data: 事件数据（变量字典）
            user: 相关用户对象（可选）
            db: 数据库会话
        
        Returns:
            执行日志列表
        
        Example:
            await EventPublisher.publish(
                event_type=EventType.USER_REGISTERED,
                data={
                    "user_name": "张三",
                    "user_email": "zhangsan@example.com",
                    "register_time": "2024-01-01 12:00:00",
                    "login_url": "https://mail.example.com/login"
                },
                user=user,
                db=db
            )
        """
        if not db:
            logger.warning(f"EventPublisher.publish called without db session for event {event_type}")
            return []
        
        try:
            from core.rule_engine import RuleEngine
            
            engine = RuleEngine(db)
            
            # 添加通用变量
            enriched_data = {
                "event_type": event_type,
                "event_time": datetime.utcnow().isoformat(),
                **data
            }
            
            # 如果有用户，添加用户信息
            if user:
                enriched_data.setdefault("user_id", user.id)
                enriched_data.setdefault("user_email", user.email)
                enriched_data.setdefault("user_name", user.display_name or user.email.split('@')[0])
            
            # 触发用户事件类型的规则
            logs = await engine.trigger_user_event(
                event_type=event_type,
                user=user,
                event_data=enriched_data
            )
            
            logger.info(f"Event {event_type} published, {len(logs)} rules triggered")
            return logs
            
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            return []
    
    @classmethod
    def get_available_events(cls) -> List[Dict[str, Any]]:
        """
        获取所有可用的事件类型（用于前端显示）
        
        Returns:
            事件类型列表，按分类分组
        """
        result = []
        for event_type, metadata in EVENT_METADATA.items():
            result.append({
                "value": event_type,
                "label": metadata["name"],
                "category": metadata["category"],
                "category_label": metadata["category_label"],
                "description": metadata["description"],
                "variables": metadata["available_variables"]
            })
        return result
    
    @classmethod
    def get_events_by_category(cls) -> Dict[str, List[Dict[str, Any]]]:
        """
        按分类获取事件类型
        
        Returns:
            按分类分组的事件字典
        """
        categories = {}
        for event in cls.get_available_events():
            cat = event["category"]
            if cat not in categories:
                categories[cat] = {
                    "label": event["category_label"],
                    "events": []
                }
            categories[cat]["events"].append({
                "value": event["value"],
                "label": event["label"],
                "variables": event["variables"]
            })
        return categories