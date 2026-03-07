"""expand_api_keys_for_secure_auth

Revision ID: 9f3c1a2b4d55
Revises: 2f4b8d7c6a11
Create Date: 2026-03-07 21:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9f3c1a2b4d55"
down_revision: Union[str, Sequence[str], None] = "2f4b8d7c6a11"
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
    if not table_exists("api_keys"):
        return

    if not column_exists("api_keys", "key_prefix"):
        op.add_column(
            "api_keys",
            sa.Column("key_prefix", sa.String(length=32), nullable=True, comment="API密钥前缀，用于快速检索"),
        )
    if not column_exists("api_keys", "expires_at"):
        op.add_column(
            "api_keys",
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True, comment="密钥过期时间"),
        )
    if not column_exists("api_keys", "revoked_at"):
        op.add_column(
            "api_keys",
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True, comment="密钥吊销时间"),
        )
    if not column_exists("api_keys", "rate_limit_per_minute"):
        op.add_column(
            "api_keys",
            sa.Column(
                "rate_limit_per_minute",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("120"),
                comment="每分钟请求速率限制",
            ),
        )
    if not column_exists("api_keys", "description"):
        op.add_column(
            "api_keys",
            sa.Column("description", sa.String(length=255), nullable=True, comment="密钥用途描述"),
        )
    if not column_exists("api_keys", "updated_at"):
        op.add_column(
            "api_keys",
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.text("now()"),
                comment="更新时间",
            ),
        )

    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE api_keys
            SET key_prefix = CASE
                WHEN key IS NULL OR key = '' THEN CONCAT('legacy_', id::text)
                ELSE LEFT(key, 16)
            END
            WHERE key_prefix IS NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE api_keys
            SET permissions = '[]'::json
            WHERE permissions IS NULL
            """
        )
    )

    op.alter_column("api_keys", "key_prefix", nullable=False)
    op.alter_column("api_keys", "rate_limit_per_minute", server_default=None)

    if not index_exists("ix_api_keys_key_prefix"):
        op.create_index("ix_api_keys_key_prefix", "api_keys", ["key_prefix"], unique=False)


def downgrade() -> None:
    if not table_exists("api_keys"):
        return

    if index_exists("ix_api_keys_key_prefix"):
        op.drop_index("ix_api_keys_key_prefix", table_name="api_keys")

    if column_exists("api_keys", "updated_at"):
        op.drop_column("api_keys", "updated_at")
    if column_exists("api_keys", "description"):
        op.drop_column("api_keys", "description")
    if column_exists("api_keys", "rate_limit_per_minute"):
        op.drop_column("api_keys", "rate_limit_per_minute")
    if column_exists("api_keys", "revoked_at"):
        op.drop_column("api_keys", "revoked_at")
    if column_exists("api_keys", "expires_at"):
        op.drop_column("api_keys", "expires_at")
    if column_exists("api_keys", "key_prefix"):
        op.drop_column("api_keys", "key_prefix")
