"""expand workflow id fields

Revision ID: e7f8a9b0c1d2
Revises: d5e6f7a8b9c0
Create Date: 2026-02-06 23:29:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e7f8a9b0c1d2'
down_revision = 'd5e6f7a8b9c0'
branch_labels = None
depends_on = None


def upgrade():
    # 扩大 workflow_nodes 表的 node_id 字段
    op.alter_column('workflow_nodes', 'node_id',
                    existing_type=sa.String(50),
                    type_=sa.String(100),
                    existing_nullable=False)
    
    # 扩大 workflow_edges 表的相关字段
    op.alter_column('workflow_edges', 'edge_id',
                    existing_type=sa.String(50),
                    type_=sa.String(150),
                    existing_nullable=False)
    op.alter_column('workflow_edges', 'source_node_id',
                    existing_type=sa.String(50),
                    type_=sa.String(100),
                    existing_nullable=False)
    op.alter_column('workflow_edges', 'target_node_id',
                    existing_type=sa.String(50),
                    type_=sa.String(100),
                    existing_nullable=False)
    
    # 扩大 workflow_node_executions 表的 node_id 字段
    op.alter_column('workflow_node_executions', 'node_id',
                    existing_type=sa.String(50),
                    type_=sa.String(100),
                    existing_nullable=False)


def downgrade():
    op.alter_column('workflow_nodes', 'node_id',
                    existing_type=sa.String(100),
                    type_=sa.String(50),
                    existing_nullable=False)
    
    op.alter_column('workflow_edges', 'edge_id',
                    existing_type=sa.String(150),
                    type_=sa.String(50),
                    existing_nullable=False)
    op.alter_column('workflow_edges', 'source_node_id',
                    existing_type=sa.String(100),
                    type_=sa.String(50),
                    existing_nullable=False)
    op.alter_column('workflow_edges', 'target_node_id',
                    existing_type=sa.String(100),
                    type_=sa.String(50),
                    existing_nullable=False)
    
    op.alter_column('workflow_node_executions', 'node_id',
                    existing_type=sa.String(100),
                    type_=sa.String(50),
                    existing_nullable=False)