"""add_temp_mailbox_lifecycle_and_policy

Revision ID: 1c9e6f4a2b31
Revises: 08d510aaf02b
Create Date: 2026-03-07 18:25:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1c9e6f4a2b31"
down_revision: Union[str, Sequence[str], None] = "08d510aaf02b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = :table_name"
        ),
        {"table_name": table_name},
    )
    return result.fetchone() is not None


def column_exists(table_name: str, column_name: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :table_name AND column_name = :column_name"
        ),
        {"table_name": table_name, "column_name": column_name},
    )
    return result.fetchone() is not None


def index_exists(index_name: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :index_name"),
        {"index_name": index_name},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    if table_exists("temp_mailboxes"):
        if not column_exists("temp_mailboxes", "status"):
            op.add_column(
                "temp_mailboxes",
                sa.Column("status", sa.String(length=32), nullable=False, server_default="active", comment="生命周期状态: active/expired_recoverable/purged"),
            )
        if not column_exists("temp_mailboxes", "expires_at"):
            op.add_column("temp_mailboxes", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True, comment="过期时间"))
        if not column_exists("temp_mailboxes", "recovery_until"):
            op.add_column("temp_mailboxes", sa.Column("recovery_until", sa.DateTime(timezone=True), nullable=True, comment="恢复截止时间"))
        if not column_exists("temp_mailboxes", "expired_at"):
            op.add_column("temp_mailboxes", sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True, comment="首次进入过期状态的时间"))
        if not column_exists("temp_mailboxes", "purged_at"):
            op.add_column("temp_mailboxes", sa.Column("purged_at", sa.DateTime(timezone=True), nullable=True, comment="被彻底清理的时间"))
        if not column_exists("temp_mailboxes", "last_extended_at"):
            op.add_column("temp_mailboxes", sa.Column("last_extended_at", sa.DateTime(timezone=True), nullable=True, comment="最近一次续期/恢复时间"))

        conn = op.get_bind()
        conn.execute(
            sa.text(
                """
                UPDATE temp_mailboxes
                SET
                  status = COALESCE(status, 'active'),
                  expires_at = COALESCE(expires_at, created_at + INTERVAL '24 hours'),
                  recovery_until = COALESCE(recovery_until, COALESCE(expires_at, created_at + INTERVAL '24 hours') + INTERVAL '10 days')
                """
            )
        )

        if not index_exists("ix_temp_mailboxes_status"):
            op.create_index("ix_temp_mailboxes_status", "temp_mailboxes", ["status"], unique=False)
        if not index_exists("ix_temp_mailboxes_expires_at"):
            op.create_index("ix_temp_mailboxes_expires_at", "temp_mailboxes", ["expires_at"], unique=False)
        if not index_exists("ix_temp_mailboxes_recovery_until"):
            op.create_index("ix_temp_mailboxes_recovery_until", "temp_mailboxes", ["recovery_until"], unique=False)
        if not index_exists("ix_temp_mailboxes_owner_status"):
            op.create_index("ix_temp_mailboxes_owner_status", "temp_mailboxes", ["owner_id", "status"], unique=False)

    if not table_exists("temp_mailbox_policies"):
        op.create_table(
            "temp_mailbox_policies",
            sa.Column("id", sa.Integer(), nullable=False, comment="策略唯一标识符（单例）"),
            sa.Column("cleanup_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true"), comment="是否启用自动清理"),
            sa.Column("ttl_hours", sa.Integer(), nullable=False, server_default=sa.text("24"), comment="临时邮箱有效期（小时）"),
            sa.Column("recoverable_days", sa.Integer(), nullable=False, server_default=sa.text("10"), comment="过期后可恢复天数"),
            sa.Column("cleanup_interval_hours", sa.Integer(), nullable=False, server_default=sa.text("24"), comment="自动清理执行周期（小时）"),
            sa.Column("cleanup_batch_size", sa.Integer(), nullable=False, server_default=sa.text("500"), comment="单次清理最大处理数量"),
            sa.Column("delete_emails_on_purge", sa.Boolean(), nullable=False, server_default=sa.text("true"), comment="清理邮箱时是否删除关联邮件"),
            sa.Column("last_cleanup_at", sa.DateTime(timezone=True), nullable=True, comment="最近一次清理执行时间"),
            sa.Column("last_cleanup_count", sa.Integer(), nullable=False, server_default=sa.text("0"), comment="最近一次清理处理数量"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()"), comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()"), comment="更新时间"),
            sa.PrimaryKeyConstraint("id"),
            comment="临时邮箱生命周期与自动清理策略配置",
        )

    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO temp_mailbox_policies (id, cleanup_enabled, ttl_hours, recoverable_days, cleanup_interval_hours, cleanup_batch_size, delete_emails_on_purge, last_cleanup_count)
            SELECT 1, true, 24, 10, 24, 500, true, 0
            WHERE NOT EXISTS (SELECT 1 FROM temp_mailbox_policies WHERE id = 1)
            """
        )
    )


def downgrade() -> None:
    if table_exists("temp_mailbox_policies"):
        op.drop_table("temp_mailbox_policies")

    if table_exists("temp_mailboxes"):
        if index_exists("ix_temp_mailboxes_owner_status"):
            op.drop_index("ix_temp_mailboxes_owner_status", table_name="temp_mailboxes")
        if index_exists("ix_temp_mailboxes_recovery_until"):
            op.drop_index("ix_temp_mailboxes_recovery_until", table_name="temp_mailboxes")
        if index_exists("ix_temp_mailboxes_expires_at"):
            op.drop_index("ix_temp_mailboxes_expires_at", table_name="temp_mailboxes")
        if index_exists("ix_temp_mailboxes_status"):
            op.drop_index("ix_temp_mailboxes_status", table_name="temp_mailboxes")

        if column_exists("temp_mailboxes", "last_extended_at"):
            op.drop_column("temp_mailboxes", "last_extended_at")
        if column_exists("temp_mailboxes", "purged_at"):
            op.drop_column("temp_mailboxes", "purged_at")
        if column_exists("temp_mailboxes", "expired_at"):
            op.drop_column("temp_mailboxes", "expired_at")
        if column_exists("temp_mailboxes", "recovery_until"):
            op.drop_column("temp_mailboxes", "recovery_until")
        if column_exists("temp_mailboxes", "expires_at"):
            op.drop_column("temp_mailboxes", "expires_at")
        if column_exists("temp_mailboxes", "status"):
            op.drop_column("temp_mailboxes", "status")
