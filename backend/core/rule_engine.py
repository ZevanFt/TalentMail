"""
自动化规则引擎 - 阶段二核心组件
负责规则触发、条件匹配、动作执行
"""
import re
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from db.models.automation import AutomationRule, AutomationLog
from db.models.email import Email, Folder
from db.models.features import Tag, EmailTag
from db.models.user import User
from core.template_engine import TemplateEngine
from core.config import settings

logger = logging.getLogger(__name__)


# ============== 触发器类型定义 ==============
class TriggerType:
    """触发器类型常量"""
    EMAIL_RECEIVED = "email_received"      # 收到邮件时触发
    EMAIL_SENT = "email_sent"              # 发送邮件时触发
    SCHEDULED = "scheduled"                # 定时触发
    USER_EVENT = "user_event"              # 用户事件触发
    MANUAL = "manual"                      # 手动触发


# ============== 条件操作符定义 ==============
class ConditionOperator:
    """条件操作符常量"""
    EQUALS = "equals"                      # 等于
    NOT_EQUALS = "not_equals"              # 不等于
    CONTAINS = "contains"                  # 包含
    NOT_CONTAINS = "not_contains"          # 不包含
    STARTS_WITH = "starts_with"            # 以...开头
    ENDS_WITH = "ends_with"                # 以...结尾
    MATCHES_REGEX = "matches_regex"        # 正则匹配
    GREATER_THAN = "greater_than"          # 大于
    LESS_THAN = "less_than"                # 小于
    IS_EMPTY = "is_empty"                  # 为空
    IS_NOT_EMPTY = "is_not_empty"          # 不为空
    IN_LIST = "in_list"                    # 在列表中
    NOT_IN_LIST = "not_in_list"            # 不在列表中


# ============== 动作类型定义 ==============
class ActionType:
    """动作类型常量"""
    SEND_EMAIL = "send_email"              # 发送邮件（直接指定内容）
    SEND_TEMPLATE_EMAIL = "send_template_email"  # 发送模板邮件（使用数据库模板）
    FORWARD_EMAIL = "forward_email"        # 转发邮件
    REPLY_EMAIL = "reply_email"            # 回复邮件
    ADD_TAG = "add_tag"                    # 添加标签
    REMOVE_TAG = "remove_tag"              # 移除标签
    MOVE_TO_FOLDER = "move_to_folder"      # 移动到文件夹
    MARK_AS_READ = "mark_as_read"          # 标记已读
    MARK_AS_STARRED = "mark_as_starred"    # 标记星标
    DELETE_EMAIL = "delete_email"          # 删除邮件
    ARCHIVE_EMAIL = "archive_email"        # 归档邮件
    SET_VARIABLE = "set_variable"          # 设置变量（用于后续动作）
    LOG_MESSAGE = "log_message"            # 记录日志
    WEBHOOK = "webhook"                    # 调用 Webhook


class RuleEngine:
    """
    规则引擎核心类
    负责规则的加载、匹配和执行
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.template_engine = TemplateEngine(db)
        self._action_handlers = self._register_action_handlers()
    
    def _register_action_handlers(self) -> Dict[str, callable]:
        """注册动作处理器"""
        return {
            ActionType.SEND_EMAIL: self._action_send_email,
            ActionType.SEND_TEMPLATE_EMAIL: self._action_send_template_email,
            ActionType.FORWARD_EMAIL: self._action_forward_email,
            ActionType.REPLY_EMAIL: self._action_reply_email,
            ActionType.ADD_TAG: self._action_add_tag,
            ActionType.REMOVE_TAG: self._action_remove_tag,
            ActionType.MOVE_TO_FOLDER: self._action_move_to_folder,
            ActionType.MARK_AS_READ: self._action_mark_as_read,
            ActionType.MARK_AS_STARRED: self._action_mark_as_starred,
            ActionType.DELETE_EMAIL: self._action_delete_email,
            ActionType.ARCHIVE_EMAIL: self._action_archive_email,
            ActionType.SET_VARIABLE: self._action_set_variable,
            ActionType.LOG_MESSAGE: self._action_log_message,
            ActionType.WEBHOOK: self._action_webhook,
        }
    
    # ============== 规则获取 ==============
    
    def get_rules_for_trigger(
        self, 
        trigger_type: str, 
        user_id: Optional[int] = None
    ) -> List[AutomationRule]:
        """
        获取指定触发器类型的所有活跃规则
        
        Args:
            trigger_type: 触发器类型
            user_id: 用户ID（可选，用于获取用户规则）
        
        Returns:
            规则列表，按优先级排序
        """
        query = self.db.query(AutomationRule).filter(
            AutomationRule.trigger_type == trigger_type,
            AutomationRule.is_active == True
        )
        
        if user_id:
            # 获取用户规则和系统规则
            query = query.filter(
                (AutomationRule.owner_id == user_id) | 
                (AutomationRule.is_system == True)
            )
        else:
            # 只获取系统规则
            query = query.filter(AutomationRule.is_system == True)
        
        return query.order_by(AutomationRule.priority.desc()).all()
    
    # ============== 触发器处理 ==============
    
    async def trigger_email_received(
        self, 
        email: Email, 
        user: User
    ) -> List[AutomationLog]:
        """
        触发邮件接收事件
        
        Args:
            email: 收到的邮件
            user: 邮件所属用户
        
        Returns:
            执行日志列表
        """
        trigger_data = self._build_email_context(email)
        trigger_data["event"] = "email_received"
        trigger_data["user_id"] = user.id
        trigger_data["user_email"] = user.email
        
        rules = self.get_rules_for_trigger(TriggerType.EMAIL_RECEIVED, user.id)
        
        logs = []
        for rule in rules:
            log = await self._execute_rule(rule, trigger_data, email=email, user=user)
            logs.append(log)
        
        return logs
    
    async def trigger_email_sent(
        self, 
        email: Email, 
        user: User
    ) -> List[AutomationLog]:
        """
        触发邮件发送事件
        """
        trigger_data = self._build_email_context(email)
        trigger_data["event"] = "email_sent"
        trigger_data["user_id"] = user.id
        trigger_data["user_email"] = user.email
        
        rules = self.get_rules_for_trigger(TriggerType.EMAIL_SENT, user.id)
        
        logs = []
        for rule in rules:
            log = await self._execute_rule(rule, trigger_data, email=email, user=user)
            logs.append(log)
        
        return logs
    
    async def trigger_user_event(
        self, 
        event_type: str, 
        user: User, 
        event_data: Dict[str, Any]
    ) -> List[AutomationLog]:
        """
        触发用户事件
        
        Args:
            event_type: 事件类型 (login/register/password_change 等)
            user: 用户
            event_data: 事件数据
        """
        trigger_data = {
            "event": event_type,
            "user_id": user.id,
            "user_email": user.email,
            "user_name": user.display_name or user.email.split('@')[0],
            **event_data
        }
        
        rules = self.get_rules_for_trigger(TriggerType.USER_EVENT, user.id)
        
        # 过滤匹配事件类型的规则
        matching_rules = []
        for rule in rules:
            config = rule.trigger_config or {}
            if config.get("event_type") == event_type or config.get("event_type") == "*":
                matching_rules.append(rule)
        
        logs = []
        for rule in matching_rules:
            log = await self._execute_rule(rule, trigger_data, user=user)
            logs.append(log)
        
        return logs
    
    async def trigger_manual(
        self, 
        rule_id: int, 
        context: Dict[str, Any],
        user: Optional[User] = None
    ) -> AutomationLog:
        """
        手动触发规则
        
        Args:
            rule_id: 规则ID
            context: 上下文数据
            user: 执行用户
        """
        rule = self.db.query(AutomationRule).filter(
            AutomationRule.id == rule_id
        ).first()
        
        if not rule:
            raise ValueError(f"Rule not found: {rule_id}")
        
        trigger_data = {
            "event": "manual",
            **context
        }
        
        if user:
            trigger_data["user_id"] = user.id
            trigger_data["user_email"] = user.email
        
        return await self._execute_rule(rule, trigger_data, user=user)
    
    # ============== 规则执行 ==============
    
    async def _execute_rule(
        self, 
        rule: AutomationRule, 
        trigger_data: Dict[str, Any],
        email: Optional[Email] = None,
        user: Optional[User] = None
    ) -> AutomationLog:
        """
        执行单个规则
        
        Args:
            rule: 规则对象
            trigger_data: 触发器数据
            email: 相关邮件（可选）
            user: 相关用户（可选）
        
        Returns:
            执行日志
        """
        start_time = time.time()
        
        # 创建日志记录
        log = AutomationLog(
            rule_id=rule.id,
            trigger_type=rule.trigger_type,
            trigger_data=trigger_data,
            conditions_matched=False,
            status="pending"
        )
        
        try:
            # 检查条件
            conditions_matched = self._check_conditions(rule.conditions, trigger_data)
            log.conditions_matched = conditions_matched
            
            if not conditions_matched:
                log.status = "skipped"
                log.execution_time_ms = int((time.time() - start_time) * 1000)
                self.db.add(log)
                self.db.commit()
                return log
            
            # 执行动作
            actions_results = []
            execution_context = {**trigger_data}  # 复制上下文，动作可以修改
            
            for action in (rule.actions or []):
                action_type = action.get("type")
                action_config = action.get("config", {})
                
                try:
                    result = await self._execute_action(
                        action_type, 
                        action_config, 
                        execution_context,
                        email=email,
                        user=user
                    )
                    actions_results.append({
                        "type": action_type,
                        "status": "success",
                        "result": result
                    })
                except Exception as e:
                    logger.error(f"Action {action_type} failed: {e}")
                    actions_results.append({
                        "type": action_type,
                        "status": "failed",
                        "error": str(e)
                    })
            
            log.actions_executed = actions_results
            
            # 判断整体状态
            failed_count = sum(1 for r in actions_results if r["status"] == "failed")
            if failed_count == 0:
                log.status = "success"
            elif failed_count == len(actions_results):
                log.status = "failed"
            else:
                log.status = "partial"
            
            # 更新规则统计
            rule.execution_count = (rule.execution_count or 0) + 1
            rule.last_executed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Rule execution failed: {e}")
            log.status = "failed"
            log.error_message = str(e)
        
        log.execution_time_ms = int((time.time() - start_time) * 1000)
        
        self.db.add(log)
        self.db.commit()
        
        return log
    
    # ============== 条件匹配 ==============
    
    def _check_conditions(
        self, 
        conditions: Optional[List[Dict]], 
        context: Dict[str, Any]
    ) -> bool:
        """
        检查所有条件是否满足（AND 关系）
        
        Args:
            conditions: 条件列表
            context: 上下文数据
        
        Returns:
            是否所有条件都满足
        """
        if not conditions:
            return True
        
        for condition in conditions:
            if not self._check_single_condition(condition, context):
                return False
        
        return True
    
    def _check_single_condition(
        self, 
        condition: Dict, 
        context: Dict[str, Any]
    ) -> bool:
        """
        检查单个条件
        
        条件格式:
        {
            "field": "sender_email",
            "operator": "contains",
            "value": "@example.com"
        }
        """
        field = condition.get("field")
        operator = condition.get("operator")
        expected_value = condition.get("value")
        
        # 获取实际值（支持嵌套字段，如 "email.subject"）
        actual_value = self._get_nested_value(context, field)
        
        # 执行比较
        return self._compare_values(actual_value, operator, expected_value)
    
    def _get_nested_value(self, data: Dict, field: str) -> Any:
        """获取嵌套字段值"""
        if not field:
            return None
        
        parts = field.split(".")
        value = data
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        
        return value
    
    def _compare_values(
        self, 
        actual: Any, 
        operator: str, 
        expected: Any
    ) -> bool:
        """比较值"""
        # 转换为字符串进行比较（对于字符串操作）
        actual_str = str(actual) if actual is not None else ""
        expected_str = str(expected) if expected is not None else ""
        
        if operator == ConditionOperator.EQUALS:
            return actual_str.lower() == expected_str.lower()
        
        elif operator == ConditionOperator.NOT_EQUALS:
            return actual_str.lower() != expected_str.lower()
        
        elif operator == ConditionOperator.CONTAINS:
            return expected_str.lower() in actual_str.lower()
        
        elif operator == ConditionOperator.NOT_CONTAINS:
            return expected_str.lower() not in actual_str.lower()
        
        elif operator == ConditionOperator.STARTS_WITH:
            return actual_str.lower().startswith(expected_str.lower())
        
        elif operator == ConditionOperator.ENDS_WITH:
            return actual_str.lower().endswith(expected_str.lower())
        
        elif operator == ConditionOperator.MATCHES_REGEX:
            try:
                return bool(re.search(expected_str, actual_str, re.IGNORECASE))
            except re.error:
                logger.warning(f"Invalid regex pattern: {expected_str}")
                return False
        
        elif operator == ConditionOperator.GREATER_THAN:
            try:
                return float(actual) > float(expected)
            except (ValueError, TypeError):
                return False
        
        elif operator == ConditionOperator.LESS_THAN:
            try:
                return float(actual) < float(expected)
            except (ValueError, TypeError):
                return False
        
        elif operator == ConditionOperator.IS_EMPTY:
            return not actual or actual_str.strip() == ""
        
        elif operator == ConditionOperator.IS_NOT_EMPTY:
            return actual and actual_str.strip() != ""
        
        elif operator == ConditionOperator.IN_LIST:
            if isinstance(expected, list):
                return actual_str.lower() in [str(v).lower() for v in expected]
            else:
                # 逗号分隔的列表
                items = [s.strip().lower() for s in expected_str.split(",")]
                return actual_str.lower() in items
        
        elif operator == ConditionOperator.NOT_IN_LIST:
            if isinstance(expected, list):
                return actual_str.lower() not in [str(v).lower() for v in expected]
            else:
                items = [s.strip().lower() for s in expected_str.split(",")]
                return actual_str.lower() not in items
        
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False
    
    # ============== 动作执行 ==============
    
    async def _execute_action(
        self, 
        action_type: str, 
        config: Dict[str, Any],
        context: Dict[str, Any],
        email: Optional[Email] = None,
        user: Optional[User] = None
    ) -> Any:
        """
        执行单个动作
        
        Args:
            action_type: 动作类型
            config: 动作配置
            context: 执行上下文
            email: 相关邮件
            user: 相关用户
        
        Returns:
            动作执行结果
        """
        handler = self._action_handlers.get(action_type)
        
        if not handler:
            raise ValueError(f"Unknown action type: {action_type}")
        
        return await handler(config, context, email, user)
    
    # ============== 动作处理器 ==============
    
    async def _action_send_email(
        self, 
        config: Dict, 
        context: Dict,
        email: Optional[Email],
        user: Optional[User]
    ) -> Dict:
        """发送邮件动作"""
        from core.mail import send_system_email
        
        to_email = self._render_value(config.get("to"), context)
        template_code = config.get("template_code")
        
        # 合并模板变量
        variables = {**context}
        if config.get("variables"):
            for key, value in config["variables"].items():
                variables[key] = self._render_value(value, context)
        
        success = await send_system_email(
            to_email=to_email,
            template_code=template_code,
            variables=variables,
            db=self.db
        )
        
        return {"sent": success, "to": to_email, "template": template_code}
    
    async def _action_send_template_email(
        self,
        config: Dict,
        context: Dict,
        email: Optional[Email],
        user: Optional[User]
    ) -> Dict:
        """
        发送模板邮件动作
        
        config 配置:
        - template_code: 模板代码 (必填)
        - to: 收件人邮箱 (支持 {{variable}} 语法)
        - to_type: 发送目标类型 (trigger_user/fixed_email/admin)
        - variables: 额外变量 (可选，会与 context 合并)
        """
        from core.mail import send_system_email
        from db.models.user import User as UserModel
        
        template_code = config.get("template_code")
        if not template_code:
            raise ValueError("template_code is required for send_template_email action")
        
        # 确定收件人
        to_type = config.get("to_type", "trigger_user")
        to_email = None
        
        if to_type == "trigger_user":
            # 发送给触发事件的用户
            to_email = context.get("user_email")
            if not to_email and user:
                to_email = user.email
        elif to_type == "fixed_email":
            # 发送给指定邮箱
            to_email = self._render_value(config.get("to"), context)
        elif to_type == "admin":
            # 发送给管理员
            admin = self.db.query(UserModel).filter(
                UserModel.is_admin == True,
                UserModel.is_active == True
            ).first()
            if admin:
                to_email = admin.email
        else:
            # 默认使用 config.to
            to_email = self._render_value(config.get("to"), context)
        
        if not to_email:
            raise ValueError(f"Cannot determine recipient email for to_type={to_type}")
        
        # 合并变量
        variables = {**context}
        if config.get("variables"):
            for key, value in config["variables"].items():
                variables[key] = self._render_value(value, context)
        
        # 发送邮件
        success = await send_system_email(
            to_email=to_email,
            template_code=template_code,
            variables=variables,
            db=self.db
        )
        
        return {
            "sent": success,
            "to": to_email,
            "template_code": template_code,
            "to_type": to_type
        }
    
    async def _action_forward_email(
        self, 
        config: Dict, 
        context: Dict,
        email: Optional[Email],
        user: Optional[User]
    ) -> Dict:
        """转发邮件动作"""
        if not email:
            raise ValueError("No email to forward")
        
        from core.mail import send_email
        from schemas.email import EmailCreate, EmailRecipient
        
        to_email = self._render_value(config.get("to"), context)
        
        # 创建转发邮件
        forward_data = EmailCreate(
            to=[EmailRecipient(email=to_email, name="")],
            cc=[],
            bcc=[],
            subject=f"Fwd: {email.subject}",
            body_html=f"""
            <p>---------- Forwarded message ----------</p>
            <p>From: {email.sender_email}</p>
            <p>Date: {email.date}</p>
            <p>Subject: {email.subject}</p>
            <p>To: {email.recipient_email}</p>
            <hr>
            {email.body_html or email.body_text or ''}
            """,
            body_text=f"""
---------- Forwarded message ----------
From: {email.sender_email}
Date: {email.date}
Subject: {email.subject}
To: {email.recipient_email}

{email.body_text or ''}
            """
        )
        
        sender = user.email if user else f"noreply@{settings.BASE_DOMAIN}"
        message_id = await send_email(forward_data, sender)
        
        return {"forwarded": bool(message_id), "to": to_email}
    
    async def _action_reply_email(
        self, 
        config: Dict, 
        context: Dict,
        email: Optional[Email],
        user: Optional[User]
    ) -> Dict:
        """回复邮件动作"""
        if not email:
            raise ValueError("No email to reply")
        
        from core.mail import send_email
        from schemas.email import EmailCreate, EmailRecipient
        
        # 渲染回复内容
        body_html = self._render_value(config.get("body_html", ""), context)
        body_text = self._render_value(config.get("body_text", ""), context)
        
        reply_data = EmailCreate(
            to=[EmailRecipient(email=email.sender_email, name=email.sender_name or "")],
            cc=[],
            bcc=[],
            subject=f"Re: {email.subject}",
            body_html=body_html,
            body_text=body_text
        )
        
        sender = user.email if user else f"noreply@{settings.BASE_DOMAIN}"
        message_id = await send_email(reply_data, sender)
        
        return {"replied": bool(message_id), "to": email.sender_email}
    
    async def _action_add_tag(
        self, 
        config: Dict, 
        context: Dict,
        email: Optional[Email],
        user: Optional[User]
    ) -> Dict:
        """添加标签动作"""
        if not email:
            raise ValueError("No email to tag")
        
        tag_name = self._render_value(config.get("tag"), context)
        
        # 查找或创建标签（Tag 已在顶部导入）
        tag = self.db.query(Tag).filter(
            Tag.name == tag_name,
            Tag.user_id == email.user_id
        ).first()
        
        if not tag:
            tag = Tag(name=tag_name, user_id=email.user_id, color="#3b82f6")
            self.db.add(tag)
            self.db.flush()
        
        # 检查是否已有此标签
        existing = self.db.query(EmailTag).filter(
            EmailTag.email_id == email.id,
            EmailTag.tag_id == tag.id
        ).first()
        
        if not existing:
            email_tag = EmailTag(email_id=email.id, tag_id=tag.id)
            self.db.add(email_tag)
        
        return {"tag_added": tag_name}
    
    async def _action_remove_tag(
        self, 
        config: Dict, 
        context: Dict,
        email: Optional[Email],
        user: Optional[User]
    ) -> Dict:
        """移除标签动作"""
        if not email:
            raise ValueError("No email to untag")
        
        tag_name = self._render_value(config.get("tag"), context)
        
        # Tag 已在顶部导入
        tag = self.db.query(Tag).filter(
            Tag.name == tag_name,
            Tag.user_id == email.user_id
        ).first()
        
        if tag:
            self.db.query(EmailTag).filter(
                EmailTag.email_id == email.id,
                EmailTag.tag_id == tag.id
            ).delete()
        
        return {"tag_removed": tag_name}
    
    async def _action_move_to_folder(
        self, 
        config: Dict, 
        context: Dict,
        email: Optional[Email],
        user: Optional[User]
    ) -> Dict:
        """移动到文件夹动作"""
        if not email:
            raise ValueError("No email to move")
        
        folder_name = self._render_value(config.get("folder"), context)
        
        # 查找文件夹（Folder 已在顶部导入）
        folder = self.db.query(Folder).filter(
            Folder.name == folder_name,
            Folder.user_id == email.user_id
        ).first()
        
        if folder:
            email.folder_id = folder.id
        else:
            # 创建文件夹
            folder = Folder(name=folder_name, user_id=email.user_id)
            self.db.add(folder)
            self.db.flush()
            email.folder_id = folder.id
        
        return {"moved_to": folder_name}
    
    async def _action_mark_as_read(
        self, 
        config: Dict, 
        context: Dict,
        email: Optional[Email],
        user: Optional[User]
    ) -> Dict:
        """标记已读动作"""
        if not email:
            raise ValueError("No email to mark")
        
        email.is_read = True
        return {"marked_read": True}
    
    async def _action_mark_as_starred(
        self, 
        config: Dict, 
        context: Dict,
        email: Optional[Email],
        user: Optional[User]
    ) -> Dict:
        """标记星标动作"""
        if not email:
            raise ValueError("No email to star")
        
        email.is_starred = True
        return {"marked_starred": True}
    
    async def _action_delete_email(
        self, 
        config: Dict, 
        context: Dict,
        email: Optional[Email],
        user: Optional[User]
    ) -> Dict:
        """删除邮件动作"""
        if not email:
            raise ValueError("No email to delete")
        
        # 软删除 - 移动到垃圾箱（Folder 已在顶部导入）
        trash_folder = self.db.query(Folder).filter(
            Folder.name == "Trash",
            Folder.user_id == email.user_id
        ).first()
        
        if trash_folder:
            email.folder_id = trash_folder.id
        else:
            # 硬删除
            email.deleted_at = datetime.utcnow()
        
        return {"deleted": True}
    
    async def _action_archive_email(
        self, 
        config: Dict, 
        context: Dict,
        email: Optional[Email],
        user: Optional[User]
    ) -> Dict:
        """归档邮件动作"""
        if not email:
            raise ValueError("No email to archive")
        
        # Folder 已在顶部导入
        archive_folder = self.db.query(Folder).filter(
            Folder.name == "Archive",
            Folder.user_id == email.user_id
        ).first()
        
        if not archive_folder:
            archive_folder = Folder(name="Archive", user_id=email.user_id)
            self.db.add(archive_folder)
            self.db.flush()
        
        email.folder_id = archive_folder.id
        return {"archived": True}
    
    async def _action_set_variable(
        self, 
        config: Dict, 
        context: Dict,
        email: Optional[Email],
        user: Optional[User]
    ) -> Dict:
        """设置变量动作（用于后续动作）"""
        var_name = config.get("name")
        var_value = self._render_value(config.get("value"), context)
        
        context[var_name] = var_value
        return {"variable_set": var_name, "value": var_value}
    
    async def _action_log_message(
        self, 
        config: Dict, 
        context: Dict,
        email: Optional[Email],
        user: Optional[User]
    ) -> Dict:
        """记录日志动作"""
        message = self._render_value(config.get("message", ""), context)
        level = config.get("level", "info")
        
        log_func = getattr(logger, level, logger.info)
        log_func(f"[RuleEngine] {message}")
        
        return {"logged": message}
    
    async def _action_webhook(
        self, 
        config: Dict, 
        context: Dict,
        email: Optional[Email],
        user: Optional[User]
    ) -> Dict:
        """调用 Webhook 动作"""
        import httpx
        
        url = self._render_value(config.get("url"), context)
        method = config.get("method", "POST").upper()
        headers = config.get("headers", {})
        
        # 构建请求体
        body = {}
        if config.get("body"):
            for key, value in config["body"].items():
                body[key] = self._render_value(value, context)
        else:
            # 默认发送上下文
            body = context
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=body,
                timeout=30.0
            )
        
        return {
            "webhook_called": url,
            "status_code": response.status_code,
            "success": response.is_success
        }
    
    # ============== 辅助方法 ==============
    
    def _build_email_context(self, email: Email) -> Dict[str, Any]:
        """构建邮件上下文"""
        return {
            "email_id": email.id,
            "message_id": email.message_id,
            "subject": email.subject or "",
            "sender_email": email.sender_email or "",
            "sender_name": email.sender_name or "",
            "recipient_email": email.recipient_email or "",
            "body_text": email.body_text or "",
            "body_html": email.body_html or "",
            "date": str(email.date) if email.date else "",
            "is_read": email.is_read,
            "is_starred": email.is_starred,
            "has_attachments": email.has_attachments,
            "folder_id": email.folder_id,
        }
    
    def _render_value(self, template: Any, context: Dict[str, Any]) -> str:
        """
        渲染模板值，支持 {{variable}} 语法
        
        Args:
            template: 模板字符串或其他值
            context: 上下文数据
        
        Returns:
            渲染后的字符串
        """
        if template is None:
            return ""
        
        if not isinstance(template, str):
            return str(template)
        
        # 使用模板引擎渲染
        return self.template_engine.render(template, context)