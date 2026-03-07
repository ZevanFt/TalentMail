"""add_spam_report_training_tracking_fields

Revision ID: 6d4e8b2a1c3f
Revises: c3b8d9e1f2a4
Create Date: 2026-03-08 12:20:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6d4e8b2a1c3f"
down_revision: Union[str, Sequence[str], None] = "c3b8d9e1f2a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    if not column_exists("spam_reports", "learn_attempts"):
        op.add_column(
            "spam_reports",
            sa.Column("learn_attempts", sa.Integer(), nullable=False, server_default="0", comment="训练尝试次数"),
        )
    if not column_exists("spam_reports", "learn_error"):
        op.add_column(
            "spam_reports",
            sa.Column("learn_error", sa.String(length=1024), nullable=True, comment="最近一次训练失败信息"),
        )
    if not column_exists("spam_reports", "learned_at"):
        op.add_column(
            "spam_reports",
            sa.Column("learned_at", sa.DateTime(timezone=True), nullable=True, comment="训练成功时间"),
        )

    op.execute("UPDATE spam_reports SET learn_attempts = 0 WHERE learn_attempts IS NULL")
    op.alter_column("spam_reports", "learn_attempts", server_default=None)


def downgrade() -> None:
    if column_exists("spam_reports", "learned_at"):
        op.drop_column("spam_reports", "learned_at")
    if column_exists("spam_reports", "learn_error"):
        op.drop_column("spam_reports", "learn_error")
    if column_exists("spam_reports", "learn_attempts"):
        op.drop_column("spam_reports", "learn_attempts")
