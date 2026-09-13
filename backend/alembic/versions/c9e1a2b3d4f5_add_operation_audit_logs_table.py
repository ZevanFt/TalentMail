"""add_operation_audit_logs_table

Revision ID: c9e1a2b3d4f5
Revises: fe1fce456023
Create Date: 2026-03-08 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9e1a2b3d4f5"
down_revision: Union[str, Sequence[str], None] = "fe1fce456023"
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
    if not table_exists("operation_audit_logs"):
        op.create_table(
            "operation_audit_logs",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="审计日志唯一标识符"),
            sa.Column("user_id", sa.Integer(), nullable=True, comment="操作用户ID"),
            sa.Column("actor_type", sa.String(length=32), nullable=False, server_default="user", comment="操作者类型"),
            sa.Column("action", sa.String(length=64), nullable=False, comment="动作标识"),
            sa.Column("resource_type", sa.String(length=64), nullable=True, comment="资源类型"),
            sa.Column("resource_id", sa.String(length=64), nullable=True, comment="资源 ID"),
            sa.Column("detail", sa.Text(), nullable=True, comment="补充信息（JSON 文本）"),
            sa.Column("ip_address", sa.String(length=64), nullable=True, comment="请求来源 IP"),
            sa.Column("user_agent", sa.String(length=255), nullable=True, comment="客户端 UA"),
            sa.Column("status", sa.String(length=16), nullable=False, server_default="success", comment="结果"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            comment="平台关键操作审计日志",
        )
    for idx, cols in (
        ("ix_op_audit_logs_user_id", ["user_id"]),
        ("ix_op_audit_logs_created_at", ["created_at"]),
        ("ix_op_audit_user_created", ["user_id", "created_at"]),
        ("ix_op_audit_action_created", ["action", "created_at"]),
    ):
        if not index_exists(idx):
            op.create_index(idx, "operation_audit_logs", cols, unique=False)


def downgrade() -> None:
    for idx in (
        "ix_op_audit_action_created",
        "ix_op_audit_user_created",
        "ix_op_audit_logs_created_at",
        "ix_op_audit_logs_user_id",
    ):
        if index_exists(idx):
            op.drop_index(idx, table_name="operation_audit_logs")
    if table_exists("operation_audit_logs"):
        op.drop_table("operation_audit_logs")
