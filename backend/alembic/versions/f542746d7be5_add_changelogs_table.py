"""add_changelogs_table

Revision ID: f542746d7be5
Revises: b8c7d6e5f4a3
Create Date: 2026-01-04 16:28:17.879138

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f542746d7be5'
down_revision: Union[str, Sequence[str], None] = 'b8c7d6e5f4a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建系统更新日志表"""
    op.create_table(
        'changelogs',
        sa.Column('id', sa.Integer(), nullable=False, comment='更新日志唯一标识符'),
        sa.Column('version', sa.String(length=50), nullable=False, comment='版本号，如 1.0.0, 1.1.0'),
        sa.Column('title', sa.String(length=255), nullable=False, comment='更新标题'),
        sa.Column('content', sa.Text(), nullable=False, comment='更新内容（支持Markdown格式）'),
        sa.Column('type', sa.String(length=50), nullable=False, server_default='release', comment='类型：release/hotfix/beta/alpha'),
        sa.Column('category', sa.String(length=50), nullable=True, comment='分类：feature/bugfix/improvement/security'),
        sa.Column('is_major', sa.Boolean(), nullable=True, server_default='false', comment='是否为重大更新'),
        sa.Column('is_published', sa.Boolean(), nullable=True, server_default='true', comment='是否已发布（未发布的只有管理员可见）'),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True, comment='发布时间'),
        sa.Column('author', sa.String(length=100), nullable=True, comment='更新作者/负责人'),
        sa.Column('tags', sa.JSON(), nullable=True, comment='标签列表，如 ["新功能", "工作流", "模板"]'),
        sa.Column('breaking_changes', sa.Text(), nullable=True, comment='破坏性变更说明'),
        sa.Column('migration_notes', sa.Text(), nullable=True, comment='迁移说明'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='系统更新日志表，记录项目版本更新历史和功能变更'
    )
    op.create_index(op.f('ix_changelogs_version'), 'changelogs', ['version'], unique=False)


def downgrade() -> None:
    """删除系统更新日志表"""
    op.drop_index(op.f('ix_changelogs_version'), table_name='changelogs')
    op.drop_table('changelogs')
