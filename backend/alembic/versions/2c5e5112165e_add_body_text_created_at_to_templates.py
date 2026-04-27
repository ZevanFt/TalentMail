"""add_body_text_created_at_to_templates

Revision ID: 2c5e5112165e
Revises: 9f203dbee7cc
Create Date: 2026-04-27 01:56:29.422198

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c5e5112165e'
down_revision: Union[str, Sequence[str], None] = '9f203dbee7cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('templates', sa.Column('body_text', sa.Text(), nullable=True, comment='模板纯文本内容'))
    op.add_column('templates', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True, comment='创建时间'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('templates', 'created_at')
    op.drop_column('templates', 'body_text')
