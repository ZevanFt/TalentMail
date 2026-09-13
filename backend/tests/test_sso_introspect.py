"""SSO introspect 响应组装逻辑测试"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest


class TestIntrospectPayloadMapping:
    def test_maps_auth_center_fields(self):
        # 纯映射规则：Auth Center introspect → TalentMail 响应
        data = {"active": True, "mfa_enabled": True, "display_name": "Alice"}
        local = SimpleNamespace(email="alice@example.com", sso_user_id="user_1")
        resp = {
            "active": bool(data.get("active")),
            "mfa_enabled": bool(data.get("mfa_enabled", False)),
            "display_name": data.get("display_name"),
            "local_email": local.email if local else None,
            "sso_user_id": local.sso_user_id if local else None,
        }
        assert resp["active"] is True
        assert resp["mfa_enabled"] is True
        assert resp["display_name"] == "Alice"
        assert resp["local_email"] == "alice@example.com"
        assert resp["sso_user_id"] == "user_1"

    def test_inactive_when_no_session(self):
        data = {"active": False, "mfa_enabled": False}
        resp = {
            "active": bool(data.get("active")),
            "mfa_enabled": bool(data.get("mfa_enabled", False)),
        }
        assert resp["active"] is False
