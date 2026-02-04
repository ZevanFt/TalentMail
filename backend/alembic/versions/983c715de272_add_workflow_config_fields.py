"""add_workflow_config_fields

Revision ID: 983c715de272
Revises: 2a48d15a1495
Create Date: 2026-02-03 17:04:31.521692

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '983c715de272'
down_revision: Union[str, Sequence[str], None] = '2a48d15a1495'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 给 workflows 表添加配置相关字段
    op.add_column('workflows', sa.Column('config_schema', sa.JSON(), nullable=True, comment='可配置项的JSON Schema'))
    op.add_column('workflows', sa.Column('default_config', sa.JSON(), nullable=True, comment='默认配置'))
    op.add_column('workflows', sa.Column('config', sa.JSON(), nullable=True, comment='当前配置'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('workflows', 'config')
    op.drop_column('workflows', 'default_config')
    op.drop_column('workflows', 'config_schema')
