"""add template_metadata and global_variables tables

Revision ID: a1b2c3d4e5f6
Revises: fc0e721cb44b
Create Date: 2024-12-29 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'fc0e721cb44b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建模板元数据表
    op.create_table(
        'template_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('trigger_description', sa.Text(), nullable=True),
        sa.Column('variables', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('default_subject', sa.String(255), nullable=True),
        sa.Column('default_body_html', sa.Text(), nullable=True),
        sa.Column('default_body_text', sa.Text(), nullable=True),
        sa.Column('is_system', sa.Boolean(), server_default='true'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        comment='模板元数据定义表，定义系统支持的所有模板类型及其变量'
    )
    op.create_index('ix_template_metadata_code', 'template_metadata', ['code'], unique=True)
    
    # 创建全局变量表
    op.create_table(
        'global_variables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(50), nullable=False),
        sa.Column('label', sa.String(100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False, server_default=''),
        sa.Column('value_type', sa.String(20), server_default='static'),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        comment='全局变量表，所有模板都可以使用的变量'
    )
    op.create_index('ix_global_variables_key', 'global_variables', ['key'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_global_variables_key', table_name='global_variables')
    op.drop_table('global_variables')
    op.drop_index('ix_template_metadata_code', table_name='template_metadata')
    op.drop_table('template_metadata')