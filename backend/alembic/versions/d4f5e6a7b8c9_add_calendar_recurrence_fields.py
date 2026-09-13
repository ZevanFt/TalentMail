"""add_calendar_recurrence_fields

Revision ID: d4f5e6a7b8c9
Revises: c9e1a2b3d4f5
Create Date: 2026-03-08 13:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4f5e6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c9e1a2b3d4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = :t AND column_name = :c"
        ),
        {"t": table_name, "c": column_name},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    if not column_exists("calendar_events", "recurrence"):
        op.add_column(
            "calendar_events",
            sa.Column("recurrence", sa.String(length=20), nullable=False, server_default="none", comment="重复规则"),
        )
    if not column_exists("calendar_events", "recurrence_until"):
        op.add_column(
            "calendar_events",
            sa.Column("recurrence_until", sa.DateTime(timezone=True), nullable=True, comment="重复截止时间"),
        )


def downgrade() -> None:
    if column_exists("calendar_events", "recurrence_until"):
        op.drop_column("calendar_events", "recurrence_until")
    if column_exists("calendar_events", "recurrence"):
        op.drop_column("calendar_events", "recurrence")
