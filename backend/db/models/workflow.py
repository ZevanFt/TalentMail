"""
工作流相关数据模型
基于飞书审批工作流设计理念，实现可视化流程配置
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base


class NodeType(Base):
    """
    节点类型定义表
    定义工作流中可用的节点类型（触发器、条件、动作等）
    """
    __tablename__ = "node_types"
    __table_args__ = {'comment': '工作流节点类型定义表'}

    id = Column(Integer, primary_key=True, index=True, comment='节点类型ID')
    code = Column(String(50), unique=True, nullable=False, comment='节点类型代码')
    name = Column(String(100), nullable=False, comment='节点类型名称(中文)')
    name_en = Column(String(100), nullable=True, comment='节点类型名称(英文)')
    category = Column(String(50), nullable=False, comment='节点分类: trigger/logic/email_action/email_operation/integration/end')
    icon = Column(String(50), nullable=True, comment='图标(emoji或图标名)')
    color = Column(String(20), nullable=True, comment='节点颜色')
    description = Column(Text, nullable=True, comment='节点描述')
    
    # 端口定义
    input_ports = Column(JSON, nullable=True, default=list, comment='输入端口定义')
    output_ports = Column(JSON, nullable=True, default=list, comment='输出端口定义')
    
    # 配置 Schema
    config_schema = Column(JSON, nullable=True, comment='节点配置的JSON Schema')
    
    # 可用变量
    available_variables = Column(JSON, nullable=True, comment='节点可使用的变量')
    output_variables = Column(JSON, nullable=True, comment='节点输出的变量')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    is_system = Column(Boolean, default=True, comment='是否系统内置')
    sort_order = Column(Integer, default=0, comment='排序')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment='更新时间')


class SystemWorkflow(Base):
    """
    系统工作流定义表
    预设的核心业务流程（如注册、登录、密码重置）
    """
    __tablename__ = "system_workflows"
    __table_args__ = {'comment': '系统工作流定义表'}

    id = Column(Integer, primary_key=True, index=True, comment='工作流ID')
    code = Column(String(100), unique=True, nullable=False, comment='工作流代码')
    name = Column(String(200), nullable=False, comment='工作流名称')
    name_en = Column(String(200), nullable=True, comment='工作流名称(英文)')
    description = Column(Text, nullable=True, comment='工作流描述')
    category = Column(String(50), nullable=False, comment='分类: auth/email/billing/file/admin')
    
    # 触发事件 (新增: 用于事件驱动)
    trigger_event = Column(String(100), unique=True, nullable=True, index=True, comment='触发事件代码')

    # 流程定义
    nodes = Column(JSON, nullable=False, default=list, comment='节点列表')
    edges = Column(JSON, nullable=False, default=list, comment='连接列表')
    
    # 配置
    config_schema = Column(JSON, nullable=True, comment='可配置项的JSON Schema')
    default_config = Column(JSON, nullable=True, default=dict, comment='默认配置')
    
    # 版本
    version = Column(Integer, default=1, comment='版本号')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 关系
    configs = relationship("SystemWorkflowConfig", back_populates="workflow", cascade="all, delete-orphan")


class SystemWorkflowConfig(Base):
    """
    系统工作流实例配置表
    管理员的自定义配置（覆盖默认配置）
    """
    __tablename__ = "system_workflow_configs"
    __table_args__ = {'comment': '系统工作流配置表'}

    id = Column(Integer, primary_key=True, index=True, comment='配置ID')
    workflow_id = Column(Integer, ForeignKey("system_workflows.id", ondelete="CASCADE"), nullable=False, comment='工作流ID')
    
    # 自定义配置
    config = Column(JSON, nullable=False, default=dict, comment='自定义配置(覆盖默认配置)')
    node_configs = Column(JSON, nullable=True, comment='各节点的自定义配置')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    version = Column(Integer, default=1, comment='版本号')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment='更新时间')
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment='创建者ID')
    
    # 关系
    workflow = relationship("SystemWorkflow", back_populates="configs")
    creator = relationship("User", foreign_keys=[created_by])


class Workflow(Base):
    """
    自定义工作流表
    用户或管理员创建的自定义工作流
    """
    __tablename__ = "workflows"
    __table_args__ = {'comment': '自定义工作流表'}

    id = Column(Integer, primary_key=True, index=True, comment='工作流ID')
    name = Column(String(200), nullable=False, comment='工作流名称')
    description = Column(Text, nullable=True, comment='工作流描述')
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, comment='创建者ID')
    
    # 分类
    scope = Column(String(20), default='personal', comment='范围: system(系统级)/personal(个人级)')
    category = Column(String(50), nullable=True, comment='分类标签')
    
    # 状态
    status = Column(String(20), default='draft', comment='状态: draft/published/disabled')
    is_active = Column(Boolean, default=False, comment='是否启用')

    # 配置
    config_schema = Column(JSON, nullable=True, comment='可配置项的JSON Schema')
    default_config = Column(JSON, nullable=True, default=dict, comment='默认配置')
    config = Column(JSON, nullable=True, default=dict, comment='当前配置')

    # 版本控制
    version = Column(Integer, default=1, comment='当前版本')
    published_version = Column(Integer, nullable=True, comment='已发布版本')
    
    # 统计
    execution_count = Column(Integer, default=0, comment='执行次数')
    last_executed_at = Column(DateTime(timezone=True), nullable=True, comment='最后执行时间')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 关系
    owner = relationship("User", back_populates="workflows")
    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    edges = relationship("WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowNode(Base):
    """
    工作流节点表
    存储工作流中的每个节点
    """
    __tablename__ = "workflow_nodes"
    __table_args__ = (
        UniqueConstraint('workflow_id', 'node_id', name='uq_workflow_node'),
        {'comment': '工作流节点表'}
    )

    id = Column(Integer, primary_key=True, index=True, comment='记录ID')
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, comment='工作流ID')
    
    # 节点信息
    node_id = Column(String(100), nullable=False, comment='节点唯一ID(前端生成)')
    node_type = Column(String(50), nullable=False, comment='节点大类: trigger/logic/action/end')
    node_subtype = Column(String(50), nullable=False, comment='节点子类型代码')
    name = Column(String(100), nullable=True, comment='节点显示名称')
    
    # 位置信息（画布坐标）
    position_x = Column(Integer, default=0, comment='X坐标')
    position_y = Column(Integer, default=0, comment='Y坐标')
    
    # 配置
    config = Column(JSON, nullable=True, default=dict, comment='节点配置')
    
    # 系统节点属性
    is_system = Column(Boolean, default=False, comment='是否系统节点(不可删除)')
    is_required = Column(Boolean, default=False, comment='是否必须节点')
    can_configure = Column(Boolean, default=True, comment='是否可配置')
    
    # 排序
    sort_order = Column(Integer, default=0, comment='执行顺序')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 关系
    workflow = relationship("Workflow", back_populates="nodes")


class WorkflowEdge(Base):
    """
    工作流连接表
    存储节点之间的连接关系
    """
    __tablename__ = "workflow_edges"
    __table_args__ = (
        UniqueConstraint('workflow_id', 'edge_id', name='uq_workflow_edge'),
        {'comment': '工作流连接表'}
    )

    id = Column(Integer, primary_key=True, index=True, comment='记录ID')
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, comment='工作流ID')
    
    # 连接信息
    edge_id = Column(String(150), nullable=False, comment='连接唯一ID(前端生成)')
    source_node_id = Column(String(100), nullable=False, comment='源节点ID')
    target_node_id = Column(String(100), nullable=False, comment='目标节点ID')
    source_handle = Column(String(50), nullable=True, comment='源节点的输出端口')
    target_handle = Column(String(50), nullable=True, comment='目标节点的输入端口')
    
    # 条件分支标签
    label = Column(String(100), nullable=True, comment='连接标签(如"是"/"否")')
    condition_key = Column(String(50), nullable=True, comment='条件键')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    
    # 关系
    workflow = relationship("Workflow", back_populates="edges")


class WorkflowExecution(Base):
    """
    工作流执行记录表
    记录每次工作流执行的信息
    """
    __tablename__ = "workflow_executions"
    __table_args__ = {'comment': '工作流执行记录表'}

    id = Column(Integer, primary_key=True, index=True, comment='执行ID')
    
    # 关联
    workflow_type = Column(String(20), nullable=False, comment='工作流类型: system/custom')
    workflow_id = Column(Integer, nullable=False, comment='工作流ID')
    workflow_version = Column(Integer, nullable=True, comment='执行时的工作流版本')
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment='关联用户ID')
    
    # 触发信息
    trigger_type = Column(String(50), nullable=True, comment='触发类型')
    trigger_data = Column(JSON, nullable=True, comment='触发数据')
    
    # 执行状态
    status = Column(String(20), nullable=False, default='pending', comment='状态: pending/running/success/failed/cancelled')
    current_node = Column(String(50), nullable=True, comment='当前执行节点')
    
    # 时间
    started_at = Column(DateTime(timezone=True), server_default=func.now(), comment='开始时间')
    finished_at = Column(DateTime(timezone=True), nullable=True, comment='结束时间')
    
    # 结果
    result = Column(JSON, nullable=True, comment='执行结果')
    error_message = Column(Text, nullable=True, comment='错误信息')
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    node_executions = relationship("WorkflowNodeExecution", back_populates="execution", cascade="all, delete-orphan")


class WorkflowNodeExecution(Base):
    """
    节点执行记录表
    记录每个节点的执行详情
    """
    __tablename__ = "workflow_node_executions"
    __table_args__ = {'comment': '工作流节点执行记录表'}

    id = Column(Integer, primary_key=True, index=True, comment='记录ID')
    execution_id = Column(Integer, ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False, comment='执行ID')
    
    node_id = Column(String(100), nullable=False, comment='节点ID')
    node_type = Column(String(50), nullable=True, comment='节点类型')
    
    # 执行信息
    started_at = Column(DateTime(timezone=True), nullable=True, comment='开始时间')
    finished_at = Column(DateTime(timezone=True), nullable=True, comment='结束时间')
    status = Column(String(20), nullable=False, default='pending', comment='状态: pending/running/success/failed/skipped')
    
    # 输入输出
    input_data = Column(JSON, nullable=True, comment='输入数据')
    output_data = Column(JSON, nullable=True, comment='输出数据')
    error_message = Column(Text, nullable=True, comment='错误信息')
    
    # 关系
    execution = relationship("WorkflowExecution", back_populates="node_executions")


class WorkflowTemplate(Base):
    """
    工作流模板表
    提供可复用的工作流模板，支持官方和社区贡献
    """
    __tablename__ = "workflow_templates"
    __table_args__ = {'comment': '工作流模板表'}

    id = Column(Integer, primary_key=True, index=True, comment='模板ID')
    name = Column(String(200), nullable=False, comment='模板名称')
    name_en = Column(String(200), nullable=True, comment='模板名称(英文)')
    description = Column(Text, nullable=True, comment='模板描述')
    description_en = Column(Text, nullable=True, comment='模板描述(英文)')
    
    # 分类
    category = Column(String(50), nullable=False, default='general', comment='分类: email/marketing/notification/integration/automation/general')
    
    # 来源类型
    source_type = Column(String(20), nullable=False, default='official', comment='来源: official(官方)/community(社区)/user(用户)')
    
    # 创建者
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment='作者ID')
    author_name = Column(String(100), nullable=True, comment='作者名称(冗余，防止用户删除后丢失)')
    
    # 工作流定义（与 SystemWorkflow 结构一致）
    nodes = Column(JSON, nullable=False, default=list, comment='节点列表')
    edges = Column(JSON, nullable=False, default=list, comment='连接列表')
    default_config = Column(JSON, nullable=True, default=dict, comment='默认配置')
    
    # 预览图
    preview_image = Column(String(500), nullable=True, comment='预览图URL')
    thumbnail = Column(String(500), nullable=True, comment='缩略图URL')
    
    # 统计
    use_count = Column(Integer, default=0, comment='使用次数')
    favorite_count = Column(Integer, default=0, comment='收藏次数')
    
    # 审核状态（社区模板需要审核）
    review_status = Column(String(20), default='pending', comment='审核状态: pending/approved/rejected')
    reviewed_at = Column(DateTime(timezone=True), nullable=True, comment='审核时间')
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment='审核人ID')
    
    # 版本
    version = Column(String(20), default='1.0.0', comment='模板版本')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    is_featured = Column(Boolean, default=False, comment='是否推荐')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 关系
    author = relationship("User", foreign_keys=[author_id], backref="workflow_templates")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    tags = relationship("WorkflowTemplateTag", back_populates="template", cascade="all, delete-orphan")
    favorites = relationship("WorkflowTemplateFavorite", back_populates="template", cascade="all, delete-orphan")


class WorkflowTemplateTag(Base):
    """
    工作流模板标签表
    支持多标签分类
    """
    __tablename__ = "workflow_template_tags"
    __table_args__ = (
        UniqueConstraint('template_id', 'tag', name='uq_template_tag'),
        {'comment': '工作流模板标签表'}
    )

    id = Column(Integer, primary_key=True, index=True, comment='记录ID')
    template_id = Column(Integer, ForeignKey("workflow_templates.id", ondelete="CASCADE"), nullable=False, comment='模板ID')
    tag = Column(String(50), nullable=False, index=True, comment='标签名')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    
    # 关系
    template = relationship("WorkflowTemplate", back_populates="tags")


class WorkflowTemplateFavorite(Base):
    """
    用户收藏模板表
    """
    __tablename__ = "workflow_template_favorites"
    __table_args__ = (
        UniqueConstraint('user_id', 'template_id', name='uq_user_template_favorite'),
        {'comment': '用户收藏模板表'}
    )

    id = Column(Integer, primary_key=True, index=True, comment='记录ID')
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment='用户ID')
    template_id = Column(Integer, ForeignKey("workflow_templates.id", ondelete="CASCADE"), nullable=False, comment='模板ID')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='收藏时间')
    
    # 关系
    user = relationship("User", backref="favorite_templates")
    template = relationship("WorkflowTemplate", back_populates="favorites")


class WorkflowVersion(Base):
    """
    工作流版本历史表
    存储每次保存时的完整快照，用于版本回溯和差异对比
    """
    __tablename__ = "workflow_versions"
    __table_args__ = {'comment': '工作流版本历史表'}

    id = Column(Integer, primary_key=True, index=True, comment='版本记录ID')
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, comment='工作流ID')
    version = Column(Integer, nullable=False, comment='版本号')
    
    # 快照数据
    nodes = Column(JSON, nullable=False, default=list, comment='节点快照')
    edges = Column(JSON, nullable=False, default=list, comment='连接快照')
    config = Column(JSON, nullable=True, comment='配置快照')
    
    # 变更信息
    change_summary = Column(Text, nullable=True, comment='变更摘要')
    
    # 创建信息
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment='创建者ID')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    
    # 关系
    workflow = relationship("Workflow", backref="versions")
    creator = relationship("User", foreign_keys=[created_by])