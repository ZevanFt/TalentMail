"""add_caldav_uid_to_calendar_events

Revision ID: e5f6a7b8c9d0
Revises: d4f5e6a7b8c9
Create Date: 2026-03-08 15:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4f5e6a7b8c9"
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


def index_exists(index_name: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :index_name"),
        {"index_name": index_name},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    if not column_exists("calendar_events", "caldav_uid"):
        op.add_column(
            "calendar_events",
            sa.Column("caldav_uid", sa.String(length=255), nullable=True, comment="CalDAV UID"),
        )
    if not index_exists("ix_calendar_events_caldav_uid"):
        op.create_index("ix_calendar_events_caldav_uid", "calendar_events", ["caldav_uid"], unique=False)


def downgrade() -> None:
    if index_exists("ix_calendar_events_caldav_uid"):
        op.drop_index("ix_calendar_events_caldav_uid", table_name="calendar_events")
    if column_exists("calendar_events", "caldav_uid"):
        op.drop_column("calendar_events", "caldav_uid")
