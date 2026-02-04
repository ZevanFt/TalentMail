"""add_spam_management_tables

Revision ID: 2a48d15a1495
Revises: 2d0614e710cb
Create Date: 2026-02-02 16:24:12.849621

添加垃圾邮件管理相关表：
1. trusted_senders - 白名单（信任的发件人）
2. spam_reports - 垃圾邮件报告/学习记录
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a48d15a1495'
down_revision: Union[str, Sequence[str], None] = '2d0614e710cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加垃圾邮件管理表"""

    # 1. 创建白名单表 - trusted_senders
    op.create_table(
        'trusted_senders',
        sa.Column('id', sa.Integer(), primary_key=True, comment='白名单记录ID'),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'),
                  nullable=False, comment='所属用户ID'),
        sa.Column('email', sa.String(255), nullable=False, comment='信任的邮箱地址（可以是完整地址或域名如 @example.com）'),
        sa.Column('sender_type', sa.String(20), nullable=False, default='email',
                  comment="类型: 'email'(完整地址) 或 'domain'(整个域名)"),
        sa.Column('note', sa.String(255), nullable=True, comment='备注'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(),
                  comment='添加时间'),
        comment='用户信任的发件人白名单'
    )

    # 创建索引
    op.create_index('ix_trusted_senders_user_id', 'trusted_senders', ['user_id'])
    op.create_index('ix_trusted_senders_email', 'trusted_senders', ['email'])

    # 2. 创建垃圾邮件报告表 - spam_reports
    op.create_table(
        'spam_reports',
        sa.Column('id', sa.Integer(), primary_key=True, comment='报告ID'),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'),
                  nullable=False, comment='报告用户ID'),
        sa.Column('email_id', sa.Integer(), sa.ForeignKey('emails.id', ondelete='CASCADE'),
                  nullable=False, comment='被报告的邮件ID'),
        sa.Column('report_type', sa.String(20), nullable=False,
                  comment="报告类型: 'spam'(标记为垃圾) 或 'ham'(标记为非垃圾)"),
        sa.Column('original_folder_id', sa.Integer(), sa.ForeignKey('folders.id'),
                  nullable=True, comment='邮件原始文件夹ID'),
        sa.Column('learned', sa.Boolean(), default=False, comment='是否已学习到 SpamAssassin'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(),
                  comment='报告时间'),
        comment='垃圾邮件报告记录，用于训练过滤器'
    )

    # 创建索引
    op.create_index('ix_spam_reports_user_id', 'spam_reports', ['user_id'])
    op.create_index('ix_spam_reports_email_id', 'spam_reports', ['email_id'])


def downgrade() -> None:
    """移除垃圾邮件管理表"""

    # ���除索引和表
    op.drop_index('ix_spam_reports_email_id', 'spam_reports')
    op.drop_index('ix_spam_reports_user_id', 'spam_reports')
    op.drop_table('spam_reports')

    op.drop_index('ix_trusted_senders_email', 'trusted_senders')
    op.drop_index('ix_trusted_senders_user_id', 'trusted_senders')
    op.drop_table('trusted_senders')
