"""操作审计与备份 API 模型/纯逻辑测试"""
from datetime import datetime, timezone
from types import SimpleNamespace

from api.admin_ops import BackupFileItem, OperationAuditItem


class TestSchemas:
    def test_operation_audit_item_fields(self):
        item = OperationAuditItem(
            id=1,
            user_id=2,
            actor_type="admin",
            action="backup.create",
            resource_type="backup",
            resource_id="f.sql.gz",
            detail=None,
            ip_address="10.0.0.1",
            status="success",
            created_at=datetime.now(timezone.utc),
        )
        assert item.action == "backup.create"
        assert item.status == "success"

    def test_backup_file_item(self):
        item = BackupFileItem(
            name="talentmail-20260308-031700.sql.gz",
            size_bytes=1024,
            modified_at=datetime.now(timezone.utc),
        )
        assert item.name.endswith(".sql.gz")
        assert item.size_bytes > 0
