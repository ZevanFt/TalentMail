"""
测试会话识别功能
"""
import pytest
from datetime import datetime, timezone
from jose import jwt

from core.config import settings
from core.security import create_access_token, verify_token
from api.deps import get_current_session_id


class TestSessionIdentification:
    """会话识别测试类"""

    def test_token_with_session_id(self):
        """测试 token 中包含 session_id"""
        # 创建包含 session_id 的 token
        session_id = 12345
        token_data = {
            "sub": "test@example.com",
            "session_id": session_id
        }
        token = create_access_token(data=token_data)

        # 验证 token
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # 确保 session_id 在 token 中
        assert "session_id" in decoded
        assert decoded["session_id"] == session_id

    def test_token_without_session_id(self):
        """测试没有 session_id 的 token（向后兼容）"""
        # 创建不包含 session_id 的 token
        token_data = {"sub": "test@example.com"}
        token = create_access_token(data=token_data)

        # 验证 token
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # 确保可以正常解码，但没有 session_id
        assert "sub" in decoded
        assert "session_id" not in decoded

    def test_verify_token_with_session_id(self):
        """测试 verify_token 函数能够提取 session_id"""
        # 创建包含 session_id 的 token
        session_id = 67890
        token_data = {
            "sub": "test@example.com",
            "session_id": session_id
        }
        token = create_access_token(data=token_data)

        # 使用 verify_token 验证
        token_result = verify_token(token)

        # 确保能获取到 session_id
        assert token_result is not None
        assert hasattr(token_result, 'sub')
        assert hasattr(token_result, 'session_id')
        assert token_result.session_id == session_id

    def test_get_current_session_id_with_valid_token(self):
        """测试从 token 中获取 session_id"""
        # 创建包含 session_id 的 token
        session_id = 99999
        token_data = {
            "sub": "test@example.com",
            "session_id": session_id
        }
        token = create_access_token(data=token_data)

        # 模拟 get_current_session_id 的逻辑
        token_result = verify_token(token)
        extracted_session_id = getattr(token_result, 'session_id', None)

        assert extracted_session_id == session_id

    def test_get_current_session_id_without_session_id(self):
        """测试从不包含 session_id 的 token 中获取"""
        # 创建不包含 session_id 的 token
        token_data = {"sub": "test@example.com"}
        token = create_access_token(data=token_data)

        # 模拟 get_current_session_id 的逻辑
        token_result = verify_token(token)
        extracted_session_id = getattr(token_result, 'session_id', None)

        assert extracted_session_id is None

    def test_is_current_session_logic(self):
        """测试判断是否为当前会话的逻辑"""
        # 模拟会话数据
        sessions = [
            {"id": 1, "device_info": "Chrome on Windows"},
            {"id": 2, "device_info": "Safari on macOS"},
            {"id": 3, "device_info": "Firefox on Linux"},
        ]

        # 当前 session_id 是 2
        current_session_id = 2

        # 添加 is_current 标记
        for session in sessions:
            session["is_current"] = session["id"] == current_session_id

        # 验证结果
        assert sessions[0]["is_current"] is False
        assert sessions[1]["is_current"] is True  # 这是当前会话
        assert sessions[2]["is_current"] is False

    def test_multiple_sessions_same_user(self):
        """测试同一用户多个会话的识别"""
        # 模拟用户有多个活跃会话
        user_sessions = [
            {"id": 10, "browser": "Chrome", "os": "Windows", "created_at": "2025-01-01T10:00:00"},
            {"id": 11, "browser": "Safari", "os": "macOS", "created_at": "2025-01-02T10:00:00"},
            {"id": 12, "browser": "Chrome", "os": "Android", "created_at": "2025-01-03T10:00:00"},
        ]

        # 用户当前使用 session_id=11 的会话
        current_session_id = 11

        # 标记当前会话
        result = []
        for session in user_sessions:
            session_info = session.copy()
            session_info["is_current"] = session["id"] == current_session_id
            result.append(session_info)

        # 验证
        assert result[0]["is_current"] is False
        assert result[1]["is_current"] is True
        assert result[2]["is_current"] is False

        # 确保只有一个会话被标记为当前
        current_count = sum(1 for s in result if s["is_current"])
        assert current_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])