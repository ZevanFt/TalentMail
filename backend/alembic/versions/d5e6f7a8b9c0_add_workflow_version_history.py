"""add workflow version history

Revision ID: d5e6f7a8b9c0
Revises: 983c715de272
Create Date: 2026-02-06 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd5e6f7a8b9c0'
down_revision = '983c715de272'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('workflow_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('nodes', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('edges', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='工作流版本历史表，保存每次保存时的完整节点和边数据'
    )
    op.create_index(op.f('ix_workflow_versions_workflow_id'), 'workflow_versions', ['workflow_id'], unique=False)
    op.create_index('ix_workflow_versions_workflow_version', 'workflow_versions', ['workflow_id', 'version'], unique=True)


def downgrade():
    op.drop_index('ix_workflow_versions_workflow_version', table_name='workflow_versions')
    op.drop_index(op.f('ix_workflow_versions_workflow_id'), table_name='workflow_versions')
    op.drop_table('workflow_versions')