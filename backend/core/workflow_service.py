"""
工作流服务核心模块
负责工作流的执行、状态管理和节点处理
"""
import logging
import json
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from db.models.workflow import (
    NodeType, SystemWorkflow, SystemWorkflowConfig,
    Workflow, WorkflowNode, WorkflowEdge,
    WorkflowExecution, WorkflowNodeExecution
)
from db.models.user import User
from db.models.system import VerificationCode, SystemEmailTemplate
from core.template_engine import TemplateEngine
from core.mail_service import MailService
from core.workflow_runtime import WorkflowEngine as RuntimeEngine
from core.workflow_runtime import WorkflowContext as RuntimeContext
from core.workflow_runtime import WorkflowDefinition, WorkflowNode, WorkflowEdge, VariableResolver

logger = logging.getLogger(__name__)

# Re-export RuntimeContext for compatibility if needed,
# but logic should migrate to proper Runtime usage.
WorkflowContext = RuntimeContext


class NodeHandler:
    """节点处理器基类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def execute(self, node_config: Dict[str, Any], context: WorkflowContext) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """
        执行节点
        Returns: (success, output_data, next_handle)
        next_handle: 用于条件节点，指示走哪个分支
        """
        raise NotImplementedError


class GenerateCodeHandler(NodeHandler):
    """生成验证码节点处理器 (Revamped)"""
    
    async def execute(self, node_config: Dict[str, Any], context: RuntimeContext) -> Dict[str, Any]:
        """
        Input Config:
          - length: int
          - type: 'numeric' | 'alphanumeric'
          - email_var: str (path to email, e.g. {{trigger.user.email}})
          - purpose: str (e.g. 'auth')
        """
        # 1. Resolve params
        length = int(node_config.get('length', 6))
        code_type = node_config.get('type', 'numeric')
        expire_minutes = int(node_config.get('expire_minutes', 15))
        purpose = node_config.get('purpose', 'auth')
        
        # Resolve email using path (critical improvement!)
        # Config key might be "email_var" -> "{{trigger.email}}"
        # We need to get the RESOLVED value.
        # Since this method is called via Engine, node_config is ALREADY resolved!
        email = node_config.get('email')
        
        # 2. Generate Logic
        if code_type == 'numeric':
            code = ''.join(random.choices(string.digits, k=length))
        else:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        
        expire_time = datetime.utcnow() + timedelta(minutes=expire_minutes)
        
        # 3. DB Persistence
        if email:
            verification = VerificationCode(
                email=email,
                code=code,
                purpose=purpose,
                expires_at=expire_time
            )
            self.db.add(verification)
            self.db.commit()
            print(f"[GenerateCodeHandler] Saved code {code} for {email}")
        else:
            print(f"[GenerateCodeHandler] No email provided, code {code} generated in memory only.")
        
        # 4. Return Output
        return {
            'value': code, # Consistent key 'value'
            'code': code,  # Alias
            'expires_at': expire_time.isoformat()
        }


class SendTemplateEmailHandler(NodeHandler):
    """发送模板邮件节点处理器 (Revamped)"""
    
    async def execute(self, node_config: Dict[str, Any], context: RuntimeContext) -> Dict[str, Any]:
        """
        Input Config (Already Resolved):
          - to: str (email address)
          - template_code: str
          - variables: dict (mapped values)
        """
        # 1. Get Params
        to_email = node_config.get('to')
        template_code = node_config.get('template_code')
        # Here 'variables' are already resolved values (e.g. code="123456")
        # passed from the workflow engine mapping
        template_vars = node_config.get('variables', {})
        
        if not to_email:
            raise ValueError("Recipient 'to' address is missing")
        
        if not template_code:
            raise ValueError("Template code is missing")
            
        # 2. Call Mail Service
        # We reuse the existing MailService. It expects:
        # - to_email
        # - template_code (for loading template)
        # - template_data (for rendering)
        try:
            mail_service = MailService(self.db)
            
            # Use the high-level send_template_email which handles loading + rendering
            await mail_service.send_template_email(
                to=to_email,
                template_code=template_code,
                template_data=template_vars
            )
            
            print(f"[SendTemplateEmailHandler] Sent {template_code} to {to_email}")
            return {
                'status': 'sent',
                'to': to_email,
                'template': template_code
            }
        except Exception as e:
            logger.error(f"Failed to send template email: {e}")
            # Re-raise so the engine catches it and marks node as failed
            raise e


class ConditionHandler(NodeHandler):
    """条件分支节点处理器"""

    async def execute(self, node_config: Dict[str, Any], context: WorkflowContext) -> Dict[str, Any]:
        conditions = node_config.get('conditions', [])
        logic = node_config.get('logic', 'and')

        results = []
        for condition in conditions:
            field = condition.get('field')
            operator = condition.get('operator')
            expected_value = condition.get('value')

            # 获取实际值
            actual_value = context.get_variable(field)

            # 评估条件
            result = self._evaluate_condition(actual_value, operator, expected_value)
            results.append(result)

        # 组合结果
        if logic == 'and':
            final_result = all(results) if results else False
        else:
            final_result = any(results) if results else False

        # 返回新格式，包含 _output_handle 用于图遍历
        return {
            'result': final_result,
            '_output_handle': 'true' if final_result else 'false'
        }
    
    def _evaluate_condition(self, actual: Any, operator: str, expected: Any) -> bool:
        """评估单个条件"""
        if operator == 'equals':
            return actual == expected
        elif operator == 'not_equals':
            return actual != expected
        elif operator == 'contains':
            return expected in str(actual) if actual else False
        elif operator == 'not_contains':
            return expected not in str(actual) if actual else True
        elif operator == 'starts_with':
            return str(actual).startswith(expected) if actual else False
        elif operator == 'ends_with':
            return str(actual).endswith(expected) if actual else False
        elif operator == 'is_empty':
            return not actual
        elif operator == 'is_not_empty':
            return bool(actual)
        elif operator == 'greater_than':
            return float(actual) > float(expected) if actual else False
        elif operator == 'less_than':
            return float(actual) < float(expected) if actual else False
        elif operator == 'matches_regex':
            import re
            return bool(re.match(expected, str(actual))) if actual else False
        return False


class CreateUserHandler(NodeHandler):
    """创建用户节点处理器"""
    
    async def execute(self, node_config: Dict[str, Any], context: WorkflowContext) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        from core.security import get_password_hash
        
        form_data = context.get_variable('form_data', {})
        
        email_field = node_config.get('email_field', 'email')
        password_field = node_config.get('password_field', 'password')
        display_name_field = node_config.get('display_name_field', 'display_name')
        
        email = form_data.get(email_field) or context.get_variable(email_field)
        password = form_data.get(password_field) or context.get_variable(password_field)
        display_name = form_data.get(display_name_field) or context.get_variable(display_name_field) or email.split('@')[0]
        
        if not email or not password:
            return False, {'error': 'Email and password are required'}, None
        
        # 检查用户是否已存在
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            return False, {'error': 'User already exists'}, None
        
        # 创建用户
        user = User(
            email=email,
            display_name=display_name,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_verified=True  # 如果通过验证码流程，则已验证
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return True, {'user_id': user.id, 'user_email': user.email}, None


class VerifyCodeHandler(NodeHandler):
    """验证码校验节点处理器"""
    
    async def execute(self, node_config: Dict[str, Any], context: WorkflowContext) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        email = context.get_variable('email') or context.get_variable('form_data', {}).get('email')
        code = context.get_variable('verification_code') or context.get_variable('form_data', {}).get('code')
        purpose = context.get_variable('verification_purpose', 'registration')
        
        if not email or not code:
            return True, {'valid': False, 'error': 'Email and code required'}, 'invalid'
        
        # 查找验证码
        verification = self.db.query(VerificationCode).filter(
            and_(
                VerificationCode.email == email,
                VerificationCode.code == code,
                VerificationCode.purpose == purpose,
                VerificationCode.is_used == False,
                VerificationCode.expires_at > datetime.utcnow()
            )
        ).first()
        
        if verification:
            # 标记为已使用
            verification.is_used = True
            verification.used_at = datetime.utcnow()
            self.db.commit()
            return True, {'valid': True}, 'valid'
        else:
            return True, {'valid': False, 'error': 'Invalid or expired code'}, 'invalid'


class VerifyPasswordHandler(NodeHandler):
    """密码校验节点处理器"""
    
    async def execute(self, node_config: Dict[str, Any], context: WorkflowContext) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        from core.security import verify_password
        
        email = context.get_variable('email') or context.get_variable('form_data', {}).get('email')
        password = context.get_variable('password') or context.get_variable('form_data', {}).get('password')
        
        if not email or not password:
            return True, {'valid': False, 'error': 'Email and password required'}, 'invalid'
        
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            return True, {'valid': False, 'error': 'User not found'}, 'invalid'
        
        if verify_password(password, user.hashed_password):
            # 将用户信息添加到上下文
            context.set_variable('user_id', user.id)
            context.set_variable('user_email', user.email)
            context.set_variable('user_name', user.display_name)
            return True, {'valid': True, 'user_id': user.id}, 'valid'
        else:
            return True, {'valid': False, 'error': 'Invalid password'}, 'invalid'


class LogHandler(NodeHandler):
    """日志记录节点处理器"""
    
    async def execute(self, node_config: Dict[str, Any], context: RuntimeContext) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        message = node_config.get('message', '')
        level = node_config.get('level', 'info')
        
        # 变量替换
        engine = TemplateEngine(self.db)
        rendered_message = engine.render(message, context.variables)
        
        if level == 'warning':
            logger.warning(f"[Workflow] {rendered_message}")
        elif level == 'error':
            logger.error(f"[Workflow] {rendered_message}")
        else:
            logger.info(f"[Workflow] {rendered_message}")
        
        return True, {'logged': True, 'message': rendered_message}, None


# ==================== 高级节点处理器 ====================

class DelayHandler(NodeHandler):
    """延时等待节点处理器

    配置示例:
    {
        "delay_seconds": 60,      # 延时秒数
        "delay_minutes": 5,       # 延时分钟数（可选，与 delay_seconds 二选一）
        "delay_until": "{{trigger.scheduled_time}}"  # 等待到指定时间（可选）
    }
    """

    async def execute(self, node_config: Dict[str, Any], context: RuntimeContext) -> Dict[str, Any]:
        import asyncio
        from datetime import datetime

        delay_seconds = node_config.get('delay_seconds', 0)
        delay_minutes = node_config.get('delay_minutes', 0)
        delay_until = node_config.get('delay_until')

        total_seconds = delay_seconds + (delay_minutes * 60)

        if delay_until:
            # 等待到指定时间
            try:
                if isinstance(delay_until, str):
                    target_time = datetime.fromisoformat(delay_until.replace('Z', '+00:00'))
                else:
                    target_time = delay_until
                now = datetime.now(target_time.tzinfo) if target_time.tzinfo else datetime.now()
                wait_seconds = (target_time - now).total_seconds()
                if wait_seconds > 0:
                    total_seconds = wait_seconds
            except Exception as e:
                logger.warning(f"[DelayHandler] 解析时间失败: {e}")

        if total_seconds > 0:
            # 最大延时限制：1小时
            total_seconds = min(total_seconds, 3600)
            logger.info(f"[DelayHandler] 等待 {total_seconds} 秒...")
            await asyncio.sleep(total_seconds)

        return {
            'delayed': True,
            'seconds': total_seconds
        }


class WebhookHandler(NodeHandler):
    """Webhook 调用节点处理器

    配置示例:
    {
        "url": "https://api.example.com/webhook",
        "method": "POST",
        "headers": {"Authorization": "Bearer {{trigger.api_key}}"},
        "body": {"email": "{{trigger.user.email}}", "event": "registration"},
        "timeout": 30
    }
    """

    async def execute(self, node_config: Dict[str, Any], context: RuntimeContext) -> Dict[str, Any]:
        import httpx

        url = node_config.get('url')
        method = node_config.get('method', 'POST').upper()
        headers = node_config.get('headers', {})
        body = node_config.get('body', {})
        timeout = node_config.get('timeout', 30)

        if not url:
            return {'success': False, 'error': 'URL is required'}

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method == 'GET':
                    response = await client.get(url, headers=headers, params=body)
                elif method == 'POST':
                    response = await client.post(url, headers=headers, json=body)
                elif method == 'PUT':
                    response = await client.put(url, headers=headers, json=body)
                elif method == 'DELETE':
                    response = await client.delete(url, headers=headers)
                else:
                    return {'success': False, 'error': f'Unsupported method: {method}'}

                # 尝试解析 JSON 响应
                try:
                    response_data = response.json()
                except Exception:
                    response_data = response.text

                return {
                    'success': response.is_success,
                    'status_code': response.status_code,
                    'response': response_data
                }

        except httpx.TimeoutException:
            return {'success': False, 'error': 'Request timeout'}
        except Exception as e:
            logger.error(f"[WebhookHandler] 请求失败: {e}")
            return {'success': False, 'error': str(e)}


class LoopHandler(NodeHandler):
    """循环执行节点处理器

    配置示例:
    {
        "items": "{{trigger.email_list}}",  # 要遍历的列表
        "item_var": "current_email",         # 当前项的变量名
        "index_var": "loop_index",           # 索引变量名
        "max_iterations": 100                # 最大迭代次数
    }

    注意：这是一个控制流节点，实际的循环逻辑由引擎处理。
    此处理器主要用于初始化循环状态。
    """

    async def execute(self, node_config: Dict[str, Any], context: RuntimeContext) -> Dict[str, Any]:
        items = node_config.get('items', [])
        item_var = node_config.get('item_var', 'item')
        index_var = node_config.get('index_var', 'index')
        max_iterations = node_config.get('max_iterations', 100)

        # 确保 items 是列表
        if isinstance(items, str):
            try:
                import json
                items = json.loads(items)
            except Exception:
                items = [items]

        if not isinstance(items, list):
            items = list(items) if hasattr(items, '__iter__') else [items]

        # 限制迭代次数
        items = items[:max_iterations]

        return {
            'items': items,
            'total': len(items),
            'item_var': item_var,
            'index_var': index_var,
            '_loop_items': items  # 引擎使用此字段进行迭代
        }


class ParallelHandler(NodeHandler):
    """并行执行节点处理器

    配置示例:
    {
        "branches": ["branch_a", "branch_b", "branch_c"],  # 并行分支的节点ID
        "wait_all": true  # 是否等待所有分支完成
    }

    注意：实际的并行执行由引擎处理（已在 GraphExecutor 中实现）。
    此节点用于标记并行分支的起点。
    """

    async def execute(self, node_config: Dict[str, Any], context: RuntimeContext) -> Dict[str, Any]:
        branches = node_config.get('branches', [])
        wait_all = node_config.get('wait_all', True)

        return {
            'parallel': True,
            'branches': branches,
            'wait_all': wait_all,
            '_parallel_branches': branches  # 引擎使用此字段启动并行执行
        }


class SwitchHandler(NodeHandler):
    """多路分支节点处理器（类似 switch-case）

    配置示例:
    {
        "expression": "{{trigger.action_type}}",
        "cases": {
            "create": "handle_create_node",
            "update": "handle_update_node",
            "delete": "handle_delete_node"
        },
        "default": "handle_default_node"
    }
    """

    async def execute(self, node_config: Dict[str, Any], context: RuntimeContext) -> Dict[str, Any]:
        expression = node_config.get('expression')
        cases = node_config.get('cases', {})
        default = node_config.get('default')

        # expression 应该已经被解析为实际值
        value = str(expression) if expression else ''

        # 查找匹配的 case
        target_node = cases.get(value, default)

        return {
            'value': value,
            'matched_case': value if value in cases else 'default',
            'target_node': target_node,
            '_output_handle': value if value in cases else 'default'
        }


class TransformHandler(NodeHandler):
    """数据转换节点处理器

    配置示例:
    {
        "input": "{{trigger.data}}",
        "operations": [
            {"type": "filter", "condition": "item.active == true"},
            {"type": "map", "expression": "item.email"},
            {"type": "sort", "key": "name", "reverse": false}
        ],
        "output_var": "processed_data"
    }
    """

    async def execute(self, node_config: Dict[str, Any], context: RuntimeContext) -> Dict[str, Any]:
        data = node_config.get('input', [])
        operations = node_config.get('operations', [])
        output_var = node_config.get('output_var', 'result')

        result = data

        for op in operations:
            op_type = op.get('type')

            if op_type == 'filter':
                # 简单过滤：检查字段是否存在或等于某值
                field = op.get('field')
                value = op.get('value')
                if field and isinstance(result, list):
                    result = [item for item in result if item.get(field) == value]

            elif op_type == 'map':
                # 提取字段
                field = op.get('field')
                if field and isinstance(result, list):
                    result = [item.get(field) if isinstance(item, dict) else item for item in result]

            elif op_type == 'sort':
                # 排序
                key = op.get('key')
                reverse = op.get('reverse', False)
                if isinstance(result, list) and key:
                    try:
                        result = sorted(result, key=lambda x: x.get(key, '') if isinstance(x, dict) else x, reverse=reverse)
                    except Exception:
                        pass

            elif op_type == 'limit':
                # 限制数量
                limit = op.get('limit', 10)
                if isinstance(result, list):
                    result = result[:limit]

            elif op_type == 'count':
                # 计数
                result = len(result) if isinstance(result, list) else 1

        return {
            output_var: result,
            'value': result
        }


class TriggerHandler(NodeHandler):
    """触发器节点处理器

    触发器是工作流的入口点，不执行实际逻辑，只是传递触发数据。
    支持的触发类型：
    - trigger_form_submit: 表单提交触发
    - trigger_email_received: 收到邮件触发
    - trigger_schedule: 定时触发
    - trigger_api: API 调用触发
    """

    async def execute(self, node_config: Dict[str, Any], context: RuntimeContext) -> Dict[str, Any]:
        """触发器节点直接传递触发数据"""
        trigger_type = node_config.get('trigger_type', 'form_submit')

        # 触发器节点的主要作用是记录触发信息
        return {
            'trigger_type': trigger_type,
            'triggered_at': datetime.utcnow().isoformat(),
            'trigger_data': context.trigger_data if hasattr(context, 'trigger_data') else {}
        }


class DataValidateHandler(NodeHandler):
    """数据验证节点处理器

    配置示例:
    {
        "rules": [
            {"field": "email", "type": "email", "required": true},
            {"field": "password", "type": "string", "min_length": 8},
            {"field": "age", "type": "number", "min": 18, "max": 120}
        ]
    }
    """

    async def execute(self, node_config: Dict[str, Any], context: RuntimeContext) -> Dict[str, Any]:
        rules = node_config.get('rules', [])
        data = node_config.get('data', {})

        # 如果 data 为空，尝试从 context 获取
        if not data and hasattr(context, 'trigger_data'):
            data = context.trigger_data

        errors = []
        validated_data = {}

        for rule in rules:
            field = rule.get('field')
            field_type = rule.get('type', 'string')
            required = rule.get('required', False)

            value = data.get(field) if isinstance(data, dict) else None

            # 检查必填
            if required and (value is None or value == ''):
                errors.append(f"{field} 是必填项")
                continue

            if value is None:
                continue

            # 类型验证
            if field_type == 'email':
                import re
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(value)):
                    errors.append(f"{field} 不是有效的邮箱地址")
                    continue

            elif field_type == 'string':
                min_len = rule.get('min_length', 0)
                max_len = rule.get('max_length', 10000)
                if len(str(value)) < min_len:
                    errors.append(f"{field} 长度不能少于 {min_len} 个字符")
                    continue
                if len(str(value)) > max_len:
                    errors.append(f"{field} 长度不能超过 {max_len} 个字符")
                    continue

            elif field_type == 'number':
                try:
                    num_value = float(value)
                    min_val = rule.get('min')
                    max_val = rule.get('max')
                    if min_val is not None and num_value < min_val:
                        errors.append(f"{field} 不能小于 {min_val}")
                        continue
                    if max_val is not None and num_value > max_val:
                        errors.append(f"{field} 不能大于 {max_val}")
                        continue
                except (ValueError, TypeError):
                    errors.append(f"{field} 必须是数字")
                    continue

            validated_data[field] = value

        is_valid = len(errors) == 0

        return {
            'valid': is_valid,
            'errors': errors,
            'validated_data': validated_data,
            '_output_handle': 'valid' if is_valid else 'invalid'
        }


class DataUpdateUserHandler(NodeHandler):
    """更新用户数据节点处理器

    配置示例:
    {
        "user_id": "{{trigger.user_id}}",
        "updates": {
            "password": "{{trigger.new_password}}",
            "email_verified": true
        }
    }
    """

    async def execute(self, node_config: Dict[str, Any], context: RuntimeContext) -> Dict[str, Any]:
        from core.security import get_password_hash

        user_id = node_config.get('user_id')
        updates = node_config.get('updates', {})

        if not user_id:
            return {'success': False, 'error': 'user_id is required'}

        try:
            user = self.db.query(User).filter(User.id == int(user_id)).first()
            if not user:
                return {'success': False, 'error': f'User {user_id} not found'}

            # 应用更新
            for key, value in updates.items():
                if key == 'password':
                    # 密码需要加密
                    user.hashed_password = get_password_hash(value)
                elif hasattr(user, key):
                    setattr(user, key, value)

            self.db.commit()

            return {
                'success': True,
                'user_id': user.id,
                'updated_fields': list(updates.keys())
            }
        except Exception as e:
            logger.error(f"[DataUpdateUserHandler] 更新用户失败: {e}")
            return {'success': False, 'error': str(e)}


class WaitHandler(NodeHandler):
    """等待节点处理器

    用于等待外部事件（如用户输入验证码）。
    在实际实现中，这需要配合状态持久化使用。

    配置示例:
    {
        "wait_for": "verification_code",
        "timeout_minutes": 15,
        "timeout_action": "expire"
    }
    """

    async def execute(self, node_config: Dict[str, Any], context: RuntimeContext) -> Dict[str, Any]:
        wait_for = node_config.get('wait_for', 'user_input')
        timeout_minutes = node_config.get('timeout_minutes', 15)

        # 在简化实现中，等待节点直接通过
        # 实际实现需要：
        # 1. 保存工作流状态
        # 2. 等待外部事件（如验证码提交）
        # 3. 恢复工作流执行

        return {
            'status': 'waiting',
            'wait_for': wait_for,
            'timeout_minutes': timeout_minutes,
            'message': f'等待 {wait_for}，超时时间 {timeout_minutes} 分钟'
        }


class EndHandler(NodeHandler):
    """结束节点处理器

    标记工作流执行结束，可以是成功或失败。

    配置示例:
    {
        "status": "success",  # 或 "failure"
        "message": "操作完成",
        "error_code": "VERIFICATION_FAILED"  # 仅失败时
    }
    """

    async def execute(self, node_config: Dict[str, Any], context: RuntimeContext) -> Dict[str, Any]:
        end_status = node_config.get('status', 'success')
        message = node_config.get('message', '')
        error_code = node_config.get('error_code')

        result = {
            'end': True,
            'status': end_status,
            'message': message,
            'completed_at': datetime.utcnow().isoformat()
        }

        if error_code:
            result['error_code'] = error_code

        return result


class WorkflowService:
    """工作流服务"""

    # 节点处理器映射
    NODE_HANDLERS = {
        # 触发器节点（全部使用 TriggerHandler）
        'trigger_form_submit': TriggerHandler,
        'trigger_email_received': TriggerHandler,
        'trigger_schedule': TriggerHandler,
        'trigger_scheduled': TriggerHandler,  # 别名
        'trigger_api': TriggerHandler,
        'trigger_user_event': TriggerHandler,
        'trigger_webhook': TriggerHandler,
        'trigger_manual': TriggerHandler,
        # 数据节点
        'data_generate_code': GenerateCodeHandler,
        'data_verify_code': VerifyCodeHandler,
        'data_verify_password': VerifyPasswordHandler,
        'data_create_user': CreateUserHandler,
        'data_update_user': DataUpdateUserHandler,
        'data_validate': DataValidateHandler,
        'data_transform': TransformHandler,
        # 动作节点
        'action_send_template': SendTemplateEmailHandler,
        'action_send_email': SendTemplateEmailHandler,  # 复用
        'action_reply': SendTemplateEmailHandler,  # 复用（可后续扩展）
        'action_forward': SendTemplateEmailHandler,  # 复用（可后续扩展）
        # 逻辑节点
        'logic_condition': ConditionHandler,
        'logic_wait': WaitHandler,
        'logic_delay': DelayHandler,  # 映射到控制流延时
        'logic_switch': SwitchHandler,  # 映射到控制流多路分支
        'logic_parallel': ParallelHandler,  # 映射到控制流并行
        # 结束节点
        'end_success': EndHandler,
        'end_failure': EndHandler,
        # 集成节点
        'integration_log': LogHandler,
        'integration_webhook': WebhookHandler,
        'integration_notify': LogHandler,  # 暂时复用日志（可后续扩展通知功能）
        'integration_trigger_workflow': TriggerHandler,  # 触发其他工作流
        # 控制流节点
        'control_delay': DelayHandler,
        'control_loop': LoopHandler,
        'control_parallel': ParallelHandler,
        'control_switch': SwitchHandler,
        # 邮件操作节点（使用通用 EndHandler，实际操作由业务代码执行）
        'operation_mark_read': EndHandler,
        'operation_mark_starred': EndHandler,
        'operation_delete': EndHandler,
        'operation_archive': EndHandler,
        'operation_move_folder': EndHandler,
        'operation_add_tag': EndHandler,
        'operation_remove_tag': EndHandler,
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_system_workflow(self, code: str) -> Optional[SystemWorkflow]:
        """获取系统工作流"""
        return self.db.query(SystemWorkflow).filter(
            SystemWorkflow.code == code,
            SystemWorkflow.is_active == True
        ).first()
    
    def get_system_workflow_config(self, workflow_id: int) -> Optional[SystemWorkflowConfig]:
        """获取系统工作流配置"""
        return self.db.query(SystemWorkflowConfig).filter(
            SystemWorkflowConfig.workflow_id == workflow_id,
            SystemWorkflowConfig.is_active == True
        ).order_by(SystemWorkflowConfig.id.desc()).first()
    
    def get_effective_config(self, workflow: SystemWorkflow) -> Dict[str, Any]:
        """获取生效的配置（默认配置 + 自定义配置）"""
        config = dict(workflow.default_config or {})

        custom_config = self.get_system_workflow_config(workflow.id)
        if custom_config:
            config.update(custom_config.config or {})

        return config

    def apply_config_bindings(
        self,
        nodes_data: List[Dict],
        config_schema: Optional[Dict],
        effective_config: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        根据 config_schema 中的 bindings 将配置值应用到节点配置
        返回: { node_id: { field: value, ... }, ... }
        """
        node_overrides: Dict[str, Dict[str, Any]] = {}

        if not config_schema or 'properties' not in config_schema:
            return node_overrides

        for config_key, prop in config_schema.get('properties', {}).items():
            bindings = prop.get('bindings', [])
            if not bindings:
                continue

            # 获取配置值（优先使用 effective_config，其次使用 default）
            config_value = effective_config.get(config_key, prop.get('default'))

            for binding in bindings:
                node_id = binding.get('nodeId')
                field = binding.get('field')

                if not node_id or not field:
                    continue

                if node_id not in node_overrides:
                    node_overrides[node_id] = {}

                node_overrides[node_id][field] = config_value
                logger.debug(f"Config binding: {config_key}={config_value} -> node[{node_id}].{field}")

        return node_overrides

    async def trigger_event(self, event_name: str, data: Dict[str, Any], user_id: Optional[int] = None):
        """
        触发事件驱动的工作流
        Args:
            event_name: 事件名称 (e.g. 'password.forgot')
            data: 上下文数据
            user_id: 关联用户
        """
        logger.info(f"Triggering event: {event_name}")
        
        # Find workflows subscribed to this event
        workflows = self.db.query(SystemWorkflow).filter(
            SystemWorkflow.trigger_event == event_name,
            SystemWorkflow.is_active == True
        ).all()
        
        if not workflows:
            logger.info(f"No active workflows found for event: {event_name}")
            return
            
        for wf in workflows:
            logger.info(f"Executing workflow {wf.code} for event {event_name}")
            # Wrap trigger data
            trigger_payload = {
                "event": event_name,
                "user": data.get('user', {}), # Flatten/Standardize structure if needed
                **data
            }
            await self.execute_system_workflow(wf.code, trigger_payload, user_id)
    
    async def execute_system_workflow(
        self,
        workflow_code: str,
        trigger_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        执行系统工作流 (Updated to use RuntimeEngine)
        """
        try:
            # 1. Load Definition from DB
            workflow = self.get_system_workflow(workflow_code)
            if not workflow:
                return False, {'error': f'Workflow {workflow_code} not found'}

            # 2. Get Effective Config (Overrides)
            config = self.get_effective_config(workflow)

            # 3. Convert DB Model to Runtime Definition
            # This is the crucial adapter step
            runtime_nodes = {}
            start_node_id = None

            nodes_data = workflow.nodes
            edges_data = workflow.edges

            # 2.5 Apply config bindings (新增: 根据 config_schema.bindings 生成节点配置覆盖)
            binding_overrides = self.apply_config_bindings(
                nodes_data,
                workflow.config_schema,
                config
            )

            # Build basic nodes map
            for n in nodes_data:
                node_id = n['node_id']
                # Merge DB config with Override Config
                node_config = n.get('config', {}).copy()

                # 应用 node_configs 覆盖 (旧方式)
                if config.get('node_configs', {}).get(node_id):
                    node_config.update(config['node_configs'][node_id])

                # 应用 bindings 覆盖 (新方式: 工作流级配置项 -> 节点字段)
                if node_id in binding_overrides:
                    node_config.update(binding_overrides[node_id])

                # Identify Start Node (Trigger)
                if n.get('node_type') == 'trigger':
                    start_node_id = node_id

                runtime_nodes[node_id] = WorkflowNode(
                    id=node_id,
                    type=n.get('node_subtype'), # Use subtype as the runtime handler key
                    label=n.get('name'),
                    config=node_config
                )

            if not start_node_id:
                raise ValueError("No trigger node found in workflow definition")

            # Link nodes using Edges
            # 升级后支持完整的图遍历，包括条件分支
            runtime_edges = []
            for edge in edges_data:
                source = edge['source_node_id']
                target = edge['target_node_id']
                runtime_edges.append(WorkflowEdge(
                    id=edge.get('edge_id', f"{source}-{target}"),
                    source_node_id=source,
                    target_node_id=target,
                    source_handle=edge.get('source_handle'),
                    target_handle=edge.get('target_handle'),
                    condition=edge.get('condition')
                ))
                # 保持向后兼容：对于简单线性流程
                if source in runtime_nodes and not runtime_nodes[source].next_node_id:
                    runtime_nodes[source].next_node_id = target

            definition = WorkflowDefinition(
                id=workflow.code,
                name=workflow.name,
                nodes=runtime_nodes,
                start_node_id=start_node_id,
                edges=runtime_edges  # 传入边列表
            )
            
            # 4. Prepare Handlers
            # We initialize handlers with DB session injected
            handlers = {
                'data_generate_code': GenerateCodeHandler(self.db).execute,
                'data_verify_code': VerifyCodeHandler(self.db).execute,
                'data_verify_password': VerifyPasswordHandler(self.db).execute,
                'data_create_user': CreateUserHandler(self.db).execute,
                'action_send_template': SendTemplateEmailHandler(self.db).execute,
                'logic_condition': ConditionHandler(self.db).execute,
                'integration_log': LogHandler(self.db).execute,
                # 邮件操作处理器
                'operation_mark_starred': self._create_email_operation_handler('star'),
                'operation_mark_read': self._create_email_operation_handler('read'),
                'action_forward': self._create_forward_handler(),
            }
            
            # 5. Execute
            engine = RuntimeEngine(definition, handlers=handlers)
            
            # Record start
            execution = WorkflowExecution(
                workflow_type='system',
                workflow_id=workflow.id,
                user_id=user_id,
                trigger_data=trigger_data,
                status='running',
                started_at=datetime.utcnow()
            )
            self.db.add(execution)
            self.db.commit()
            
            try:
                final_context = await engine.run(trigger_data)
                
                execution.status = 'success'
                execution.finished_at = datetime.utcnow()
                # Persist the final state
                execution.result = final_context.data
                self.db.commit()
                
                return True, final_context.data
                
            except Exception as e:
                execution.status = 'failed'
                execution.error_message = str(e)
                execution.finished_at = datetime.utcnow()
                self.db.commit()
                raise e
                
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            return False, {'error': str(e)}
    
    # ==================== CRUD 操作 ====================
    
    def list_system_workflows(self) -> List[SystemWorkflow]:
        """列出所有系统工作流"""
        return self.db.query(SystemWorkflow).filter(
            SystemWorkflow.is_active == True
        ).all()
    
    def list_node_types(self, category: Optional[str] = None) -> List[NodeType]:
        """列出节点类型"""
        query = self.db.query(NodeType).filter(NodeType.is_active == True)
        if category:
            query = query.filter(NodeType.category == category)
        return query.order_by(NodeType.sort_order).all()
    
    def update_system_workflow_config(
        self,
        workflow_id: int,
        config: Dict[str, Any],
        node_configs: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None
    ) -> SystemWorkflowConfig:
        """更新系统工作流配置"""
        # 禁用旧配置
        self.db.query(SystemWorkflowConfig).filter(
            SystemWorkflowConfig.workflow_id == workflow_id,
            SystemWorkflowConfig.is_active == True
        ).update({'is_active': False})
        
        # 创建新配置
        new_config = SystemWorkflowConfig(
            workflow_id=workflow_id,
            config=config,
            node_configs=node_configs,
            is_active=True,
            created_by=created_by
        )
        self.db.add(new_config)
        self.db.commit()
        self.db.refresh(new_config)
        
        return new_config
    
    def get_workflow_executions(
        self,
        workflow_type: Optional[str] = None,
        workflow_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[WorkflowExecution]:
        """获取工作流执行记录"""
        query = self.db.query(WorkflowExecution)
        
        if workflow_type:
            query = query.filter(WorkflowExecution.workflow_type == workflow_type)
        if workflow_id:
            query = query.filter(WorkflowExecution.workflow_id == workflow_id)
        if status:
            query = query.filter(WorkflowExecution.status == status)
        
        return query.order_by(WorkflowExecution.started_at.desc()).limit(limit).all()

    def create_example_workflow(self, user_id: int) -> Optional[Workflow]:
        """为新用户创建示例工作流"""
        try:
            # 1. 创建工作流
            workflow = Workflow(
                name="[示例] 自动标记重要邮件",
                description="当收到主题包含 'Urgent' 的邮件时，自动标记为星标并转发给我",
                owner_id=user_id,
                scope='personal',
                category='email',
                status='draft',
                version=1,
                is_active=True
            )
            self.db.add(workflow)
            self.db.commit()
            self.db.refresh(workflow)
            
            # 2. 创建节点
            nodes_data = [
                {
                    "node_id": "trigger_1",
                    "node_type": "trigger",
                    "node_subtype": "trigger_email_received",
                    "name": "收到邮件",
                    "position_x": 250,
                    "position_y": 50,
                    "config": {}
                },
                {
                    "node_id": "condition_urgent",
                    "node_type": "logic",
                    "node_subtype": "logic_condition",
                    "name": "是紧急邮件？",
                    "position_x": 250,
                    "position_y": 150,
                    "config": {
                        "conditions": [
                            {"field": "subject", "operator": "contains", "value": "Urgent"}
                        ]
                    }
                },
                {
                    "node_id": "action_star",
                    "node_type": "email_operation",
                    "node_subtype": "operation_mark_starred",
                    "name": "标记星标",
                    "position_x": 100,
                    "position_y": 300,
                    "config": {}
                },
                {
                    "node_id": "action_forward",
                    "node_type": "email_action",
                    "node_subtype": "action_forward",
                    "name": "转发给自己",
                    "position_x": 100,
                    "position_y": 420,
                    "config": {
                        "to": "me@example.com",
                        "add_note": "自动转发的紧急邮件"
                    }
                },
                {
                    "node_id": "end_done",
                    "node_type": "end",
                    "node_subtype": "end_success",
                    "name": "处理完成",
                    "position_x": 100,
                    "position_y": 540,
                    "config": {"message": "已标记并转发"}
                },
                {
                    "node_id": "end_skip",
                    "node_type": "end",
                    "node_subtype": "end_success",
                    "name": "忽略",
                    "position_x": 400,
                    "position_y": 300,
                    "config": {"message": "非紧急邮件，忽略"}
                }
            ]
            
            for n in nodes_data:
                node = WorkflowNode(
                    workflow_id=workflow.id,
                    node_id=n["node_id"],
                    node_type=n["node_type"],
                    node_subtype=n["node_subtype"],
                    name=n["name"],
                    position_x=n["position_x"],
                    position_y=n["position_y"],
                    config=n["config"]
                )
                self.db.add(node)
                
            # 3. 创建边
            edges_data = [
                {"edge_id": "e1", "source": "trigger_1", "target": "condition_urgent"},
                {"edge_id": "e2", "source": "condition_urgent", "target": "action_star", "handle": "true", "label": "是"},
                {"edge_id": "e3", "source": "condition_urgent", "target": "end_skip", "handle": "false", "label": "否"},
                {"edge_id": "e4", "source": "action_star", "target": "action_forward"},
                {"edge_id": "e5", "source": "action_forward", "target": "end_done"}
            ]

            from db.models.workflow import WorkflowEdge as DBWorkflowEdge
            for e in edges_data:
                edge = DBWorkflowEdge(
                    workflow_id=workflow.id,
                    edge_id=e["edge_id"],
                    source_node_id=e["source"],
                    target_node_id=e["target"],
                    source_handle=e.get("handle"),
                    label=e.get("label")
                )
                self.db.add(edge)
                
            self.db.commit()
            return workflow

        except Exception as e:
            logger.error(f"Failed to create example workflow: {e}")
            self.db.rollback()
            return None

    def _create_email_operation_handler(self, operation: str):
        """创建邮件操作处理器"""
        async def handler(config: Dict[str, Any], context: RuntimeContext) -> Dict[str, Any]:
            email_id = config.get('email_id') or context.get_variable('trigger.email_id')
            if not email_id:
                return {'success': False, 'error': 'No email_id provided'}

            from db.models.email import Email
            email = self.db.query(Email).filter(Email.id == email_id).first()
            if not email:
                return {'success': False, 'error': f'Email {email_id} not found'}

            if operation == 'star':
                email.is_starred = True
            elif operation == 'read':
                email.is_read = True
            elif operation == 'unread':
                email.is_read = False

            self.db.commit()
            return {'success': True, 'operation': operation, 'email_id': email_id}

        return handler

    def _create_forward_handler(self):
        """创建转发邮件处理器"""
        async def handler(config: Dict[str, Any], context: RuntimeContext) -> Dict[str, Any]:
            to_email = config.get('to')
            email_id = config.get('email_id') or context.get_variable('trigger.email_id')
            add_note = config.get('add_note', '')

            if not to_email:
                return {'success': False, 'error': 'No recipient specified'}

            # 这里简化实现，实际应调用邮件发送服务
            logger.info(f"[Workflow] Forward email {email_id} to {to_email} with note: {add_note}")
            return {'success': True, 'forwarded_to': to_email, 'email_id': email_id}

        return handler