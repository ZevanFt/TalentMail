"""add_external_account_id_to_emails_and_sync_fields

Revision ID: 04012a65cc1b
Revises: 6d4e8b2a1c3f
Create Date: 2026-04-27 01:34:31.765737

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '04012a65cc1b'
down_revision: Union[str, Sequence[str], None] = '6d4e8b2a1c3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Feature #1: 外部邮箱同步 — 新增字段
    # emails 表添加 external_account_id (外部账户关联)
    op.add_column('emails', sa.Column('external_account_id', sa.Integer(), nullable=True,
                                       comment='关联的外部账户ID（外部同步的邮件）'))
    op.create_foreign_key('fk_emails_external_account_id', 'emails', 'external_accounts',
                          ['external_account_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_emails_external_account_id'), 'emails', ['external_account_id'], unique=False)

    # external_accounts 表添加增量同步字段
    op.add_column('external_accounts', sa.Column('last_uid', sa.Integer(), nullable=True,
                                                  comment='上次同步的IMAP UID，用于增量拉取'))
    op.add_column('external_accounts', sa.Column('sync_fail_count', sa.Integer(), server_default='0',
                                                  comment='连续同步失败次数，达到3次自动禁用'))

    # 自动生成的索引补齐（create_all 遗漏的）
    op.create_index(op.f('ix_attachments_email_id'), 'attachments', ['email_id'], unique=False)
    op.create_index(op.f('ix_attachments_user_id'), 'attachments', ['user_id'], unique=False)
    op.create_index(op.f('ix_drive_files_user_id'), 'drive_files', ['user_id'], unique=False)
    op.create_index(op.f('ix_emails_message_id'), 'emails', ['message_id'], unique=False)
    op.create_index(op.f('ix_emails_snoozed_until'), 'emails', ['snoozed_until'], unique=False)
    op.create_index(op.f('ix_subscriptions_plan_id'), 'subscriptions', ['plan_id'], unique=False)
    op.create_index(op.f('ix_subscriptions_user_id'), 'subscriptions', ['user_id'], unique=False)
    op.create_index(op.f('ix_temp_mailboxes_owner_id'), 'temp_mailboxes', ['owner_id'], unique=False)
    op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # 索引回滚
    op.drop_index(op.f('ix_user_sessions_user_id'), table_name='user_sessions')
    op.drop_index(op.f('ix_temp_mailboxes_owner_id'), table_name='temp_mailboxes')
    op.drop_index(op.f('ix_subscriptions_user_id'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_plan_id'), table_name='subscriptions')
    op.drop_index(op.f('ix_emails_snoozed_until'), table_name='emails')
    op.drop_index(op.f('ix_emails_message_id'), table_name='emails')
    op.drop_index(op.f('ix_drive_files_user_id'), table_name='drive_files')
    op.drop_index(op.f('ix_attachments_user_id'), table_name='attachments')
    op.drop_index(op.f('ix_attachments_email_id'), table_name='attachments')

    # Feature #1 字段回滚
    op.drop_column('external_accounts', 'sync_fail_count')
    op.drop_column('external_accounts', 'last_uid')
    op.drop_index(op.f('ix_emails_external_account_id'), table_name='emails')
    op.drop_constraint('fk_emails_external_account_id', 'emails', type_='foreignkey')
    op.drop_column('emails', 'external_account_id')
