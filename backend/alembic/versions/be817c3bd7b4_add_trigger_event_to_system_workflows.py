"""add trigger_event to system_workflows

Revision ID: be817c3bd7b4
Revises: c7d8e9f0a1b2
Create Date: 2026-01-02 17:11:29.341209

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be817c3bd7b4'
down_revision: Union[str, Sequence[str], None] = 'c7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('system_workflows', sa.Column('trigger_event', sa.String(length=100), nullable=True, comment='触发事件代码'))
    op.create_index(op.f('ix_system_workflows_trigger_event'), 'system_workflows', ['trigger_event'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_system_workflows_trigger_event'), table_name='system_workflows')
    op.drop_column('system_workflows', 'trigger_event')
