"""add_sso_user_id_to_users

Revision ID: fe1fce456023
Revises: b32ebb27ede4
Create Date: 2026-04-27 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe1fce456023'
down_revision: Union[str, Sequence[str], None] = 'b32ebb27ede4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add sso_user_id column to users table for auth-center SSO integration."""
    op.add_column('users', sa.Column(
        'sso_user_id',
        sa.String(length=64),
        nullable=True,
        comment='auth-center SSO 用户 ID (user_xxxx)',
    ))
    op.create_index(
        op.f('ix_users_sso_user_id'),
        'users',
        ['sso_user_id'],
        unique=True,
    )


def downgrade() -> None:
    """Remove sso_user_id column from users table."""
    op.drop_index(op.f('ix_users_sso_user_id'), table_name='users')
    op.drop_column('users', 'sso_user_id')
