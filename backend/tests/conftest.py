"""
pytest 配置文件
"""
import pytest
import sys
import os

# 将 backend 目录添加到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
