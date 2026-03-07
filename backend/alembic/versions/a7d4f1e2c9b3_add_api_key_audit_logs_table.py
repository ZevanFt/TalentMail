"""add_api_key_audit_logs_table

Revision ID: a7d4f1e2c9b3
Revises: 9f3c1a2b4d55
Create Date: 2026-03-07 21:40:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7d4f1e2c9b3"
down_revision: Union[str, Sequence[str], None] = "9f3c1a2b4d55"
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


def index_exists(index_name: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :index_name"),
        {"index_name": index_name},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    if not table_exists("api_key_audit_logs"):
        op.create_table(
            "api_key_audit_logs",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="审计日志唯一标识符"),
            sa.Column("api_key_id", sa.Integer(), nullable=True, comment="关联的 API Key ID"),
            sa.Column("user_id", sa.Integer(), nullable=True, comment="调用用户ID"),
            sa.Column("method", sa.String(length=16), nullable=True, comment="HTTP 方法"),
            sa.Column("path", sa.String(length=255), nullable=True, comment="请求路径"),
            sa.Column("ip_address", sa.String(length=64), nullable=True, comment="请求来源 IP"),
            sa.Column("status_code", sa.Integer(), nullable=True, comment="响应状态码"),
            sa.Column("decision", sa.String(length=32), nullable=False, comment="决策结果: allow/deny"),
            sa.Column("error_code", sa.String(length=64), nullable=True, comment="错误类型标识"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
            sa.ForeignKeyConstraint(["api_key_id"], ["api_keys.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            comment="API Key 调用审计日志",
        )

    if not index_exists("ix_api_key_audit_logs_api_key_id"):
        op.create_index("ix_api_key_audit_logs_api_key_id", "api_key_audit_logs", ["api_key_id"], unique=False)
    if not index_exists("ix_api_key_audit_logs_user_id"):
        op.create_index("ix_api_key_audit_logs_user_id", "api_key_audit_logs", ["user_id"], unique=False)
    if not index_exists("ix_api_key_audit_logs_created_at"):
        op.create_index("ix_api_key_audit_logs_created_at", "api_key_audit_logs", ["created_at"], unique=False)


def downgrade() -> None:
    if not table_exists("api_key_audit_logs"):
        return

    if index_exists("ix_api_key_audit_logs_created_at"):
        op.drop_index("ix_api_key_audit_logs_created_at", table_name="api_key_audit_logs")
    if index_exists("ix_api_key_audit_logs_user_id"):
        op.drop_index("ix_api_key_audit_logs_user_id", table_name="api_key_audit_logs")
    if index_exists("ix_api_key_audit_logs_api_key_id"):
        op.drop_index("ix_api_key_audit_logs_api_key_id", table_name="api_key_audit_logs")
    op.drop_table("api_key_audit_logs")
