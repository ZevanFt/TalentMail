"""
pytest 配置文件
"""
import os
import sys
from pathlib import Path

# 将 backend 目录添加到 Python 路径
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

# 在导入任何依赖 settings 的模块前，补齐测试用环境变量
_test_env = {
    "ADMIN_PASSWORD": "test-admin-password",
    "POSTGRES_USER": "test",
    "POSTGRES_PASSWORD": "test",
    "POSTGRES_DB": "talentmail_test",
    "DATABASE_URL_DOCKER": "postgresql+psycopg2://test:test@localhost:5432/talentmail_test",
    "SECRET_KEY": "test-secret-key-not-for-production",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    "REFRESH_TOKEN_EXPIRE_DAYS": "7",
    "JWT_ALGORITHM": "HS256",
    "ENCRYPTION_KEY": "",
    "CURRENT_ENVIRONMENT": "development",
}
for _k, _v in _test_env.items():
    os.environ.setdefault(_k, _v)

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_session():
    """创建模拟数据库会话"""
    from unittest.mock import Mock
    db = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    db.delete = Mock()
    db.query = Mock()
    return db


@pytest.fixture
def mock_user():
    """创建模拟用户"""
    from unittest.mock import Mock
    user = Mock()
    user.id = 1
    user.email = "test@example.com"
    user.display_name = "Test User"
    user.is_active = True
    user.is_admin = False
    return user


@pytest.fixture
def mock_folder():
    """创建模拟文件夹"""
    from unittest.mock import Mock
    folder = Mock()
    folder.id = 1
    folder.name = "Inbox"
    folder.role = "inbox"
    folder.user_id = 1
    return folder


@pytest.fixture
def mock_email():
    """创建模拟邮件"""
    from unittest.mock import Mock
    from datetime import datetime, timezone

    email = Mock()
    email.id = 1
    email.subject = "Test Subject"
    email.from_address = "sender@example.com"
    email.to_addresses = ["recipient@example.com"]
    email.body_text = "Test body"
    email.body_html = "<p>Test body</p>"
    email.is_read = False
    email.is_starred = False
    email.folder_id = 1
    email.received_at = datetime.now(timezone.utc)
    return email
