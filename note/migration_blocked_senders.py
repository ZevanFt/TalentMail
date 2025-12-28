"""add blocked_senders table and auto_clean settings

Revision ID: a1b2c3d4e5f6
Revises: fc0e721cb44b
Create Date: 2025-12-28

将此文件复制到 backend/alembic/versions/ 目录
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'fc0e721cb44b'
branch_labels = None
depends_on = None


def upgrade():
    # 创建黑名单表
    op.create_table('blocked_senders',
        sa.Column('id', sa.Integer(), nullable=False, comment='黑名单记录ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='所属用户ID'),
        sa.Column('email', sa.String(length=255), nullable=False, comment='被屏蔽的邮箱地址'),
        sa.Column('reason', sa.String(length=255), nullable=True, comment='屏蔽原因'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), comment='添加时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='用户屏蔽的发件人黑名单'
    )
    op.create_index(op.f('ix_blocked_senders_user_id'), 'blocked_senders', ['user_id'], unique=False)
    
    # 添加自动清理设置字段到 users 表
    op.add_column('users', sa.Column('auto_clean_trash', sa.Boolean(), server_default='true', comment='是否自动清空垃圾箱（30天）'))
    op.add_column('users', sa.Column('auto_archive_old', sa.Boolean(), server_default='false', comment='是否自动归档旧邮件（1年）'))


def downgrade():
    op.drop_column('users', 'auto_archive_old')
    op.drop_column('users', 'auto_clean_trash')
    op.drop_index(op.f('ix_blocked_senders_user_id'), table_name='blocked_senders')
    op.drop_table('blocked_senders')