"""操作审计写入测试"""
from types import SimpleNamespace
from unittest.mock import Mock, patch

from core.audit import record_operation


class TestRecordOperation:
    def test_writes_success_log(self):
        db = Mock()
        record_operation(
            db,
            action="auth.login",
            user_id=1,
            resource_type="session",
            resource_id=9,
            detail={"email": "a@b.c"},
            ip_address="1.2.3.4",
        )
        assert db.add.called
        assert db.commit.called
        added = db.add.call_args[0][0]
        assert added.action == "auth.login"
        assert added.user_id == 1
        assert added.status == "success"
        assert "a@b.c" in added.detail

    def test_swallows_commit_error(self):
        db = Mock()
        db.commit.side_effect = RuntimeError("db down")
        # 不应抛出
        record_operation(db, action="x", user_id=1)

    def test_string_detail_truncated(self):
        db = Mock()
        record_operation(db, action="x", detail="y" * 5000)
        added = db.add.call_args[0][0]
        assert len(added.detail) == 2000
