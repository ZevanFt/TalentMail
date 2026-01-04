"""add workflow tables

Revision ID: c7d8e9f0a1b2
Revises: 251ba12e58ec
Create Date: 2026-01-02 12:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, Sequence[str], None] = '251ba12e58ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # 1. 创建节点类型定义表
    op.create_table(
        'node_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('name_en', sa.String(100), nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('input_ports', sa.JSON(), nullable=True, default=[]),
        sa.Column('output_ports', sa.JSON(), nullable=True, default=[]),
        sa.Column('config_schema', sa.JSON(), nullable=True),
        sa.Column('available_variables', sa.JSON(), nullable=True),
        sa.Column('output_variables', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_system', sa.Boolean(), nullable=True, default=True),
        sa.Column('sort_order', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        comment='工作流节点类型定义表'
    )
    op.create_index('ix_node_types_id', 'node_types', ['id'], unique=False)
    
    # 2. 创建系统工作流定义表
    op.create_table(
        'system_workflows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('name_en', sa.String(200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('nodes', sa.JSON(), nullable=False, default=[]),
        sa.Column('edges', sa.JSON(), nullable=False, default=[]),
        sa.Column('config_schema', sa.JSON(), nullable=True),
        sa.Column('default_config', sa.JSON(), nullable=True, default={}),
        sa.Column('version', sa.Integer(), nullable=True, default=1),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        comment='系统工作流定义表'
    )
    op.create_index('ix_system_workflows_id', 'system_workflows', ['id'], unique=False)
    
    # 3. 创建系统工作流配置表
    op.create_table(
        'system_workflow_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False, default={}),
        sa.Column('node_configs', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('version', sa.Integer(), nullable=True, default=1),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['workflow_id'], ['system_workflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='系统工作流配置表'
    )
    op.create_index('ix_system_workflow_configs_id', 'system_workflow_configs', ['id'], unique=False)
    
    # 4. 创建自定义工作流表
    op.create_table(
        'workflows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('scope', sa.String(20), nullable=True, default='personal'),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, default='draft'),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=False),
        sa.Column('version', sa.Integer(), nullable=True, default=1),
        sa.Column('published_version', sa.Integer(), nullable=True),
        sa.Column('execution_count', sa.Integer(), nullable=True, default=0),
        sa.Column('last_executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='自定义工作流表'
    )
    op.create_index('ix_workflows_id', 'workflows', ['id'], unique=False)
    
    # 5. 创建工作流节点表
    op.create_table(
        'workflow_nodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.String(50), nullable=False),
        sa.Column('node_type', sa.String(50), nullable=False),
        sa.Column('node_subtype', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('position_x', sa.Integer(), nullable=True, default=0),
        sa.Column('position_y', sa.Integer(), nullable=True, default=0),
        sa.Column('config', sa.JSON(), nullable=True, default={}),
        sa.Column('is_system', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_required', sa.Boolean(), nullable=True, default=False),
        sa.Column('can_configure', sa.Boolean(), nullable=True, default=True),
        sa.Column('sort_order', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workflow_id', 'node_id', name='uq_workflow_node'),
        comment='工作流节点表'
    )
    op.create_index('ix_workflow_nodes_id', 'workflow_nodes', ['id'], unique=False)
    
    # 6. 创建工作流连接表
    op.create_table(
        'workflow_edges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('edge_id', sa.String(50), nullable=False),
        sa.Column('source_node_id', sa.String(50), nullable=False),
        sa.Column('target_node_id', sa.String(50), nullable=False),
        sa.Column('source_handle', sa.String(50), nullable=True),
        sa.Column('target_handle', sa.String(50), nullable=True),
        sa.Column('label', sa.String(100), nullable=True),
        sa.Column('condition_key', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workflow_id', 'edge_id', name='uq_workflow_edge'),
        comment='工作流连接表'
    )
    op.create_index('ix_workflow_edges_id', 'workflow_edges', ['id'], unique=False)
    
    # 7. 创建工作流执行记录表
    op.create_table(
        'workflow_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_type', sa.String(20), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('workflow_version', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('trigger_type', sa.String(50), nullable=True),
        sa.Column('trigger_data', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('current_node', sa.String(50), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='工作流执行记录表'
    )
    op.create_index('ix_workflow_executions_id', 'workflow_executions', ['id'], unique=False)
    
    # 8. 创建节点执行记录表
    op.create_table(
        'workflow_node_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('execution_id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.String(50), nullable=False),
        sa.Column('node_type', sa.String(50), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['execution_id'], ['workflow_executions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='工作流节点执行记录表'
    )
    op.create_index('ix_workflow_node_executions_id', 'workflow_node_executions', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('workflow_node_executions')
    op.drop_table('workflow_executions')
    op.drop_table('workflow_edges')
    op.drop_table('workflow_nodes')
    op.drop_table('workflows')
    op.drop_table('system_workflow_configs')
    op.drop_table('system_workflows')
    op.drop_table('node_types')