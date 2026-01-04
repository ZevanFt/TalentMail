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
from core.workflow_runtime import WorkflowDefinition, WorkflowNode, VariableResolver

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
    
    async def execute(self, node_config: Dict[str, Any], context: WorkflowContext) -> Tuple[bool, Dict[str, Any], Optional[str]]:
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
        
        return True, {'result': final_result}, 'true' if final_result else 'false'
    
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


class WorkflowService:
    """工作流服务"""
    
    # 节点处理器映射
    NODE_HANDLERS = {
        'data_generate_code': GenerateCodeHandler,
        'data_verify_code': VerifyCodeHandler,
        'data_verify_password': VerifyPasswordHandler,
        'data_create_user': CreateUserHandler,
        'action_send_template': SendTemplateEmailHandler,
        'logic_condition': ConditionHandler,
        'integration_log': LogHandler,
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
            
            # Build basic nodes map
            for n in nodes_data:
                node_id = n['node_id']
                # Merge DB config with Override Config
                node_config = n.get('config', {}).copy()
                if config.get('node_configs', {}).get(node_id):
                    node_config.update(config['node_configs'][node_id])
                
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
            # Note: Current RuntimeEngine assumes linear flow (next_node_id).
            # For this MVP, we map the first outgoing edge.
            # TODO: Upgrade RuntimeEngine to support full graph traversal
            for edge in edges_data:
                source = edge['source_node_id']
                target = edge['target_node_id']
                if source in runtime_nodes:
                    runtime_nodes[source].next_node_id = target
            
            definition = WorkflowDefinition(
                id=workflow.code,
                name=workflow.name,
                nodes=runtime_nodes,
                start_node_id=start_node_id
            )
            
            # 4. Prepare Handlers
            # We initialize handlers with DB session injected
            handlers = {
                'data_generate_code': GenerateCodeHandler(self.db).execute,
                'action_send_template': SendTemplateEmailHandler(self.db).execute,
                # Add more handlers as migrated...
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
            
            for e in edges_data:
                edge = WorkflowEdge(
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