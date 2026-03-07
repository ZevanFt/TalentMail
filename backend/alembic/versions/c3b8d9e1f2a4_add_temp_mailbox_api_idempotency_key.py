"""add_temp_mailbox_api_idempotency_key

Revision ID: c3b8d9e1f2a4
Revises: a7d4f1e2c9b3
Create Date: 2026-03-07 22:05:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3b8d9e1f2a4"
down_revision: Union[str, Sequence[str], None] = "a7d4f1e2c9b3"
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
    if not table_exists("temp_mailboxes"):
        return

    if not column_exists("temp_mailboxes", "api_idempotency_key"):
        op.add_column(
            "temp_mailboxes",
            sa.Column("api_idempotency_key", sa.String(length=128), nullable=True, comment="API 创建时的幂等键"),
        )

    if not index_exists("ix_temp_mailboxes_api_idempotency_key"):
        op.create_index("ix_temp_mailboxes_api_idempotency_key", "temp_mailboxes", ["api_idempotency_key"], unique=False)
    if not index_exists("uq_temp_mailboxes_owner_idempotency_key"):
        op.create_index(
            "uq_temp_mailboxes_owner_idempotency_key",
            "temp_mailboxes",
            ["owner_id", "api_idempotency_key"],
            unique=True,
            postgresql_where=sa.text("api_idempotency_key IS NOT NULL"),
        )


def downgrade() -> None:
    if not table_exists("temp_mailboxes"):
        return

    if index_exists("uq_temp_mailboxes_owner_idempotency_key"):
        op.drop_index("uq_temp_mailboxes_owner_idempotency_key", table_name="temp_mailboxes")
    if index_exists("ix_temp_mailboxes_api_idempotency_key"):
        op.drop_index("ix_temp_mailboxes_api_idempotency_key", table_name="temp_mailboxes")
    if column_exists("temp_mailboxes", "api_idempotency_key"):
        op.drop_column("temp_mailboxes", "api_idempotency_key")
