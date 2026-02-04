"""
工作流节点处理器测试
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import asyncio

# Import handlers
from core.workflow_service import (
    NodeHandler,
    GenerateCodeHandler,
    ConditionHandler,
    SendTemplateEmailHandler,
)


class MockRuntimeContext:
    """模拟工作流运行时上下文"""

    def __init__(self, variables: dict = None):
        self._variables = variables or {}
        self.trigger_data = {}

    def get_variable(self, path: str):
        """获取变量值"""
        parts = path.split('.')
        value = self._variables
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value

    def set_variable(self, path: str, value):
        """设置变量值"""
        self._variables[path] = value


class TestGenerateCodeHandler:
    """验证码生成处理器测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = Mock()
        db.add = Mock()
        db.commit = Mock()
        return db

    @pytest.mark.asyncio
    async def test_generate_numeric_code(self, mock_db):
        """测试生成数字验证码"""
        handler = GenerateCodeHandler(mock_db)
        context = MockRuntimeContext()

        config = {
            'length': 6,
            'type': 'numeric',
            'email': 'test@example.com',
            'purpose': 'auth'
        }

        result = await handler.execute(config, context)

        assert 'code' in result
        assert 'value' in result
        assert len(result['code']) == 6
        assert result['code'].isdigit()
        assert 'expires_at' in result
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_alphanumeric_code(self, mock_db):
        """测试生成字母数字验证码"""
        handler = GenerateCodeHandler(mock_db)
        context = MockRuntimeContext()

        config = {
            'length': 8,
            'type': 'alphanumeric',
            'email': 'test@example.com',
            'purpose': 'reset_password'
        }

        result = await handler.execute(config, context)

        assert len(result['code']) == 8
        assert result['code'].isalnum()

    @pytest.mark.asyncio
    async def test_generate_code_without_email(self, mock_db):
        """测试不提供邮箱时生成验证码（仅内存）"""
        handler = GenerateCodeHandler(mock_db)
        context = MockRuntimeContext()

        config = {
            'length': 4,
            'type': 'numeric'
        }

        result = await handler.execute(config, context)

        assert 'code' in result
        assert len(result['code']) == 4
        # 不应该调用数据库
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_code_custom_expiry(self, mock_db):
        """测试自定义过期时间"""
        handler = GenerateCodeHandler(mock_db)
        context = MockRuntimeContext()

        config = {
            'length': 6,
            'type': 'numeric',
            'email': 'test@example.com',
            'expire_minutes': 30
        }

        result = await handler.execute(config, context)

        expires_at = datetime.fromisoformat(result['expires_at'])
        now = datetime.utcnow()
        # 验证过期时间大约在30分钟后
        assert (expires_at - now).total_seconds() > 29 * 60
        assert (expires_at - now).total_seconds() < 31 * 60


class TestConditionHandler:
    """条件节点处理器测试"""

    @pytest.fixture
    def mock_db(self):
        return Mock()

    @pytest.mark.asyncio
    async def test_equals_condition_true(self, mock_db):
        """测试等于条件 - 满足"""
        handler = ConditionHandler(mock_db)
        context = MockRuntimeContext({'user': {'status': 'active'}})

        config = {
            'conditions': [
                {'field': 'user.status', 'operator': 'equals', 'value': 'active'}
            ],
            'logic': 'and'
        }

        result = await handler.execute(config, context)

        assert result['result'] is True
        assert result['_output_handle'] == 'true'

    @pytest.mark.asyncio
    async def test_equals_condition_false(self, mock_db):
        """测试等于条件 - 不满足"""
        handler = ConditionHandler(mock_db)
        context = MockRuntimeContext({'user': {'status': 'inactive'}})

        config = {
            'conditions': [
                {'field': 'user.status', 'operator': 'equals', 'value': 'active'}
            ],
            'logic': 'and'
        }

        result = await handler.execute(config, context)

        assert result['result'] is False
        assert result['_output_handle'] == 'false'

    @pytest.mark.asyncio
    async def test_contains_condition(self, mock_db):
        """测试包含条件"""
        handler = ConditionHandler(mock_db)
        context = MockRuntimeContext({'email': 'user@example.com'})

        config = {
            'conditions': [
                {'field': 'email', 'operator': 'contains', 'value': '@example.com'}
            ]
        }

        result = await handler.execute(config, context)

        assert result['result'] is True

    @pytest.mark.asyncio
    async def test_multiple_conditions_and_logic(self, mock_db):
        """测试多条件 AND 逻辑"""
        handler = ConditionHandler(mock_db)
        context = MockRuntimeContext({
            'user': {'status': 'active', 'role': 'admin'}
        })

        config = {
            'conditions': [
                {'field': 'user.status', 'operator': 'equals', 'value': 'active'},
                {'field': 'user.role', 'operator': 'equals', 'value': 'admin'}
            ],
            'logic': 'and'
        }

        result = await handler.execute(config, context)

        assert result['result'] is True

    @pytest.mark.asyncio
    async def test_multiple_conditions_or_logic(self, mock_db):
        """测试多条件 OR 逻辑"""
        handler = ConditionHandler(mock_db)
        context = MockRuntimeContext({
            'user': {'status': 'inactive', 'role': 'admin'}
        })

        config = {
            'conditions': [
                {'field': 'user.status', 'operator': 'equals', 'value': 'active'},
                {'field': 'user.role', 'operator': 'equals', 'value': 'admin'}
            ],
            'logic': 'or'
        }

        result = await handler.execute(config, context)

        assert result['result'] is True  # admin 条件满足

    @pytest.mark.asyncio
    async def test_is_empty_condition(self, mock_db):
        """测试空值检查条件"""
        handler = ConditionHandler(mock_db)
        context = MockRuntimeContext({'field': None})

        config = {
            'conditions': [
                {'field': 'field', 'operator': 'is_empty', 'value': None}
            ]
        }

        result = await handler.execute(config, context)

        assert result['result'] is True

    @pytest.mark.asyncio
    async def test_starts_with_condition(self, mock_db):
        """测试前缀匹配条件"""
        handler = ConditionHandler(mock_db)
        context = MockRuntimeContext({'phone': '+86-13800138000'})

        config = {
            'conditions': [
                {'field': 'phone', 'operator': 'starts_with', 'value': '+86'}
            ]
        }

        result = await handler.execute(config, context)

        assert result['result'] is True


class TestSendTemplateEmailHandler:
    """发送模板邮件处理器测试"""

    @pytest.fixture
    def mock_db(self):
        return Mock()

    @pytest.mark.asyncio
    async def test_send_email_missing_to(self, mock_db):
        """测试缺少收件人地址"""
        handler = SendTemplateEmailHandler(mock_db)
        context = MockRuntimeContext()

        config = {
            'template_code': 'welcome_email',
            'variables': {'name': 'Test User'}
        }

        with pytest.raises(ValueError, match="Recipient 'to' address is missing"):
            await handler.execute(config, context)

    @pytest.mark.asyncio
    async def test_send_email_missing_template(self, mock_db):
        """测试缺少模板代码"""
        handler = SendTemplateEmailHandler(mock_db)
        context = MockRuntimeContext()

        config = {
            'to': 'user@example.com',
            'variables': {'name': 'Test User'}
        }

        with pytest.raises(ValueError, match="Template code is missing"):
            await handler.execute(config, context)

    @pytest.mark.asyncio
    async def test_send_email_success(self, mock_db):
        """测试成功发送邮件"""
        handler = SendTemplateEmailHandler(mock_db)
        context = MockRuntimeContext()

        config = {
            'to': 'user@example.com',
            'template_code': 'welcome_email',
            'variables': {'name': 'Test User', 'code': '123456'}
        }

        # Mock MailService
        with patch('core.workflow_service.MailService') as MockMailService:
            mock_mail_service = AsyncMock()
            MockMailService.return_value = mock_mail_service

            result = await handler.execute(config, context)

            assert result['status'] == 'sent'
            assert result['to'] == 'user@example.com'
            assert result['template'] == 'welcome_email'
            mock_mail_service.send_template_email.assert_called_once_with(
                to='user@example.com',
                template_code='welcome_email',
                template_data={'name': 'Test User', 'code': '123456'}
            )


class TestNodeHandlerIntegration:
    """节点处理器集成测试"""

    def test_all_handlers_in_node_handlers_map(self):
        """测试所有处理器都在 NODE_HANDLERS 映射中"""
        from core.workflow_service import WorkflowService

        # NODE_HANDLERS 是 WorkflowService 的类属性
        NODE_HANDLERS = WorkflowService.NODE_HANDLERS

        # 确保有足够的处理器
        assert len(NODE_HANDLERS) >= 30

        # 检查关键节点类型
        critical_types = [
            'trigger_form_submit',
            'trigger_email_received',
            'data_generate_code',
            'data_verify_code',
            'action_send_template',
            'logic_condition',
            'end_success',
        ]

        for node_type in critical_types:
            assert node_type in NODE_HANDLERS, f"Missing handler for {node_type}"
            assert issubclass(NODE_HANDLERS[node_type], NodeHandler)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
