"""add_folder_support_to_drive_files

Revision ID: 82debdab9597
Revises: 2c5e5112165e
Create Date: 2026-04-27 21:53:33.931413

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82debdab9597'
down_revision: Union[str, Sequence[str], None] = '2c5e5112165e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加 parent_id 列（自引用外键，用于文件夹层级）
    op.add_column('drive_files', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_drive_files_parent_id'), 'drive_files', ['parent_id'], unique=False)
    op.create_foreign_key('fk_drive_files_parent_id', 'drive_files', 'drive_files', ['parent_id'], ['id'], ondelete='CASCADE')

    # 添加 is_folder 列
    op.add_column('drive_files', sa.Column('is_folder', sa.Boolean(), nullable=False, server_default=sa.text('false')))

    # 添加 updated_at 列
    op.add_column('drive_files', sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=True))

    # storage_path 允许 NULL（文件夹没有存储路径）
    op.alter_column('drive_files', 'storage_path', existing_type=sa.String(500), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('drive_files', 'storage_path', existing_type=sa.String(500), nullable=False)
    op.drop_column('drive_files', 'updated_at')
    op.drop_column('drive_files', 'is_folder')
    op.drop_constraint('fk_drive_files_parent_id', 'drive_files', type_='foreignkey')
    op.drop_index(op.f('ix_drive_files_parent_id'), table_name='drive_files')
    op.drop_column('drive_files', 'parent_id')
