"""add workflow templates tables

Revision ID: b8c7d6e5f4a3
Revises: be817c3bd7b4
Create Date: 2026-01-04 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8c7d6e5f4a3'
down_revision = 'be817c3bd7b4'  # 接续工作流触发事件迁移之后
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建工作流模板表
    op.create_table(
        'workflow_templates',
        sa.Column('id', sa.Integer(), nullable=False, comment='模板ID'),
        sa.Column('name', sa.String(200), nullable=False, comment='模板名称'),
        sa.Column('name_en', sa.String(200), nullable=True, comment='模板名称(英文)'),
        sa.Column('description', sa.Text(), nullable=True, comment='模板描述'),
        sa.Column('description_en', sa.Text(), nullable=True, comment='模板描述(英文)'),
        sa.Column('category', sa.String(50), nullable=False, server_default='general', comment='分类: email/marketing/notification/integration/automation/general'),
        sa.Column('source_type', sa.String(20), nullable=False, server_default='official', comment='来源: official(官方)/community(社区)/user(用户)'),
        sa.Column('author_id', sa.Integer(), nullable=True, comment='作者ID'),
        sa.Column('author_name', sa.String(100), nullable=True, comment='作者名称(冗余，防止用户删除后丢失)'),
        sa.Column('nodes', sa.JSON(), nullable=False, comment='节点列表'),
        sa.Column('edges', sa.JSON(), nullable=False, comment='连接列表'),
        sa.Column('default_config', sa.JSON(), nullable=True, comment='默认配置'),
        sa.Column('preview_image', sa.String(500), nullable=True, comment='预览图URL'),
        sa.Column('thumbnail', sa.String(500), nullable=True, comment='缩略图URL'),
        sa.Column('use_count', sa.Integer(), nullable=False, server_default='0', comment='使用次数'),
        sa.Column('favorite_count', sa.Integer(), nullable=False, server_default='0', comment='收藏次数'),
        sa.Column('review_status', sa.String(20), nullable=False, server_default='pending', comment='审核状态: pending/approved/rejected'),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True, comment='审核时间'),
        sa.Column('reviewed_by', sa.Integer(), nullable=True, comment='审核人ID'),
        sa.Column('version', sa.String(20), nullable=False, server_default='1.0.0', comment='模板版本'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='是否启用'),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='false', comment='是否推荐'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
        comment='工作流模板表'
    )
    op.create_index('ix_workflow_templates_id', 'workflow_templates', ['id'])
    op.create_index('ix_workflow_templates_category', 'workflow_templates', ['category'])
    op.create_index('ix_workflow_templates_source_type', 'workflow_templates', ['source_type'])
    op.create_index('ix_workflow_templates_review_status', 'workflow_templates', ['review_status'])
    
    # 创建工作流模板标签表
    op.create_table(
        'workflow_template_tags',
        sa.Column('id', sa.Integer(), nullable=False, comment='记录ID'),
        sa.Column('template_id', sa.Integer(), nullable=False, comment='模板ID'),
        sa.Column('tag', sa.String(50), nullable=False, comment='标签名'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), comment='创建时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['template_id'], ['workflow_templates.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('template_id', 'tag', name='uq_template_tag'),
        comment='工作流模板标签表'
    )
    op.create_index('ix_workflow_template_tags_id', 'workflow_template_tags', ['id'])
    op.create_index('ix_workflow_template_tags_tag', 'workflow_template_tags', ['tag'])
    
    # 创建用户收藏模板表
    op.create_table(
        'workflow_template_favorites',
        sa.Column('id', sa.Integer(), nullable=False, comment='记录ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('template_id', sa.Integer(), nullable=False, comment='模板ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), comment='收藏时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['workflow_templates.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'template_id', name='uq_user_template_favorite'),
        comment='用户收藏模板表'
    )
    op.create_index('ix_workflow_template_favorites_id', 'workflow_template_favorites', ['id'])


def downgrade() -> None:
    op.drop_table('workflow_template_favorites')
    op.drop_table('workflow_template_tags')
    op.drop_table('workflow_templates')