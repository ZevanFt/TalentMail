"""
工作流 API 端点
提供工作流管理和执行的 REST API
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db.database import get_db
from api.deps import get_current_user, get_current_admin_user
from db.models.user import User
from db.models.workflow import (
    NodeType, SystemWorkflow, SystemWorkflowConfig,
    Workflow, WorkflowNode, WorkflowEdge,
    WorkflowExecution, WorkflowNodeExecution,
    WorkflowVersion
)
from core.workflow_service import WorkflowService

router = APIRouter()


# ==================== Schemas ====================

class NodeTypeResponse(BaseModel):
    id: int
    code: str
    name: str
    name_en: Optional[str]
    category: str
    icon: Optional[str]
    color: Optional[str]
    description: Optional[str]
    input_ports: Optional[List]
    output_ports: Optional[List]
    config_schema: Optional[Dict]
    output_variables: Optional[List]
    
    class Config:
        from_attributes = True


class SystemWorkflowResponse(BaseModel):
    id: int
    code: str
    name: str
    name_en: Optional[str]
    description: Optional[str]
    category: str
    nodes: List[Dict]
    edges: List[Dict]
    config_schema: Optional[Dict]
    default_config: Optional[Dict]
    version: int
    is_active: bool
    
    class Config:
        from_attributes = True


class SystemWorkflowConfigUpdate(BaseModel):
    config: Dict[str, Any]
    node_configs: Optional[Dict[str, Any]] = None


class SystemWorkflowConfigResponse(BaseModel):
    id: int
    workflow_id: int
    config: Dict
    node_configs: Optional[Dict]
    is_active: bool
    version: int
    
    class Config:
        from_attributes = True


class ExecuteWorkflowRequest(BaseModel):
    trigger_data: Dict[str, Any]


class WorkflowExecutionResponse(BaseModel):
    id: int
    workflow_type: str
    workflow_id: int
    workflow_version: Optional[int]
    user_id: Optional[int]
    trigger_type: Optional[str]
    status: str
    current_node: Optional[str]
    started_at: Optional[str]
    finished_at: Optional[str]
    result: Optional[Dict]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


class NodeExecutionResponse(BaseModel):
    id: int
    node_id: str
    node_type: Optional[str]
    status: str
    started_at: Optional[str]
    finished_at: Optional[str]
    input_data: Optional[Dict]
    output_data: Optional[Dict]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


# ==================== 节点类型 API ====================

@router.get("/node-types", response_model=List[NodeTypeResponse])
async def list_node_types(
    category: Optional[str] = Query(None, description="节点分类过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有节点类型"""
    service = WorkflowService(db)
    return service.list_node_types(category)


@router.get("/node-types/{code}", response_model=NodeTypeResponse)
async def get_node_type(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个节点类型详情"""
    node_type = db.query(NodeType).filter(
        NodeType.code == code,
        NodeType.is_active == True
    ).first()
    
    if not node_type:
        raise HTTPException(status_code=404, detail="Node type not found")
    
    return node_type


# ==================== 系统工作流 API ====================

@router.get("/system", response_model=List[SystemWorkflowResponse])
async def list_system_workflows(
    category: Optional[str] = Query(None, description="分类过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取所有系统工作流（仅管理员）"""
    query = db.query(SystemWorkflow).filter(SystemWorkflow.is_active == True)
    if category:
        query = query.filter(SystemWorkflow.category == category)
    return query.all()


@router.get("/system/{code}", response_model=SystemWorkflowResponse)
async def get_system_workflow(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取单个系统工作流详情（仅管理员）"""
    workflow = db.query(SystemWorkflow).filter(
        SystemWorkflow.code == code,
        SystemWorkflow.is_active == True
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="System workflow not found")
    
    return workflow


@router.get("/system/{code}/config", response_model=Dict)
async def get_system_workflow_effective_config(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取系统工作流的生效配置（仅管理员）"""
    service = WorkflowService(db)
    workflow = service.get_system_workflow(code)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="System workflow not found")
    
    config = service.get_effective_config(workflow)
    custom_config = service.get_system_workflow_config(workflow.id)
    
    return {
        'workflow_id': workflow.id,
        'workflow_code': workflow.code,
        'config_schema': workflow.config_schema,
        'default_config': workflow.default_config,
        'custom_config': custom_config.config if custom_config else None,
        'effective_config': config
    }


@router.put("/system/{code}/config", response_model=SystemWorkflowConfigResponse)
async def update_system_workflow_config(
    code: str,
    data: SystemWorkflowConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新系统工作流配置（仅管理员）"""
    service = WorkflowService(db)
    workflow = service.get_system_workflow(code)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="System workflow not found")
    
    config = service.update_system_workflow_config(
        workflow_id=workflow.id,
        config=data.config,
        node_configs=data.node_configs,
        created_by=current_user.id
    )
    
    return config


@router.post("/system/{code}/execute")
async def execute_system_workflow(
    code: str,
    data: ExecuteWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """手动执行系统工作流（仅管理员，用于测试）"""
    service = WorkflowService(db)
    
    success, result = await service.execute_system_workflow(
        workflow_code=code,
        trigger_data=data.trigger_data,
        user_id=current_user.id
    )
    
    return {
        'success': success,
        'result': result
    }


# ==================== 执行记录 API ====================

@router.get("/executions", response_model=List[WorkflowExecutionResponse])
async def list_workflow_executions(
    workflow_type: Optional[str] = Query(None, description="工作流类型: system/custom"),
    workflow_id: Optional[int] = Query(None, description="工作流ID"),
    status: Optional[str] = Query(None, description="状态过滤"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取工作流执行记录（仅管理员）"""
    service = WorkflowService(db)
    executions = service.get_workflow_executions(
        workflow_type=workflow_type,
        workflow_id=workflow_id,
        status=status,
        limit=limit
    )
    
    return executions


@router.get("/executions/{execution_id}", response_model=Dict)
async def get_workflow_execution_detail(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取工作流执行详情（仅管理员）"""
    execution = db.query(WorkflowExecution).filter(
        WorkflowExecution.id == execution_id
    ).first()
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    # 获取节点执行记录
    node_executions = db.query(WorkflowNodeExecution).filter(
        WorkflowNodeExecution.execution_id == execution_id
    ).order_by(WorkflowNodeExecution.started_at).all()
    
    return {
        'execution': {
            'id': execution.id,
            'workflow_type': execution.workflow_type,
            'workflow_id': execution.workflow_id,
            'workflow_version': execution.workflow_version,
            'user_id': execution.user_id,
            'trigger_type': execution.trigger_type,
            'trigger_data': execution.trigger_data,
            'status': execution.status,
            'current_node': execution.current_node,
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'finished_at': execution.finished_at.isoformat() if execution.finished_at else None,
            'result': execution.result,
            'error_message': execution.error_message
        },
        'node_executions': [
            {
                'id': ne.id,
                'node_id': ne.node_id,
                'node_type': ne.node_type,
                'status': ne.status,
                'started_at': ne.started_at.isoformat() if ne.started_at else None,
                'finished_at': ne.finished_at.isoformat() if ne.finished_at else None,
                'input_data': ne.input_data,
                'output_data': ne.output_data,
                'error_message': ne.error_message
            }
            for ne in node_executions
        ]
    }


# ==================== 用户工作流 API（自定义工作流） ====================

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    config_schema: Optional[Dict] = None
    default_config: Optional[Dict] = None
    config: Optional[Dict] = None


class WorkflowNodeCreate(BaseModel):
    node_id: str
    node_type: str
    node_subtype: str
    name: Optional[str] = None
    position_x: int = 0
    position_y: int = 0
    config: Optional[Dict] = None


class WorkflowEdgeCreate(BaseModel):
    edge_id: str
    source_node_id: str
    target_node_id: str
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None
    label: Optional[str] = None


class WorkflowSaveRequest(BaseModel):
    nodes: List[WorkflowNodeCreate]
    edges: List[WorkflowEdgeCreate]


class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: Optional[int]
    scope: str
    category: Optional[str]
    status: str
    is_active: bool
    version: int
    execution_count: int
    config_schema: Optional[Dict] = None
    default_config: Optional[Dict] = None
    config: Optional[Dict] = None

    class Config:
        from_attributes = True


@router.post("/", response_model=WorkflowResponse)
async def create_workflow(
    data: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建自定义工作流"""
    workflow = Workflow(
        name=data.name,
        description=data.description,
        owner_id=current_user.id,
        scope='personal',
        category=data.category,
        status='draft'
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    
    return workflow


@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    scope: Optional[str] = Query(None, description="范围: personal/system"),
    status: Optional[str] = Query(None, description="状态: draft/published/disabled"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的工作流列表"""
    query = db.query(Workflow).filter(Workflow.owner_id == current_user.id)
    
    if scope:
        query = query.filter(Workflow.scope == scope)
    if status:
        query = query.filter(Workflow.status == status)
    
    return query.order_by(Workflow.updated_at.desc()).all()


@router.get("/{workflow_id}", response_model=Dict)
async def get_workflow_detail(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流详情（包含节点和边）"""
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.owner_id == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    nodes = db.query(WorkflowNode).filter(
        WorkflowNode.workflow_id == workflow_id
    ).all()
    
    edges = db.query(WorkflowEdge).filter(
        WorkflowEdge.workflow_id == workflow_id
    ).all()
    
    return {
        'workflow': {
            'id': workflow.id,
            'name': workflow.name,
            'description': workflow.description,
            'scope': workflow.scope,
            'category': workflow.category,
            'status': workflow.status,
            'is_active': workflow.is_active,
            'version': workflow.version,
            'config_schema': workflow.config_schema,
            'default_config': workflow.default_config,
            'config': workflow.config
        },
        'nodes': [
            {
                'node_id': n.node_id,
                'node_type': n.node_type,
                'node_subtype': n.node_subtype,
                'name': n.name,
                'position_x': n.position_x,
                'position_y': n.position_y,
                'config': n.config
            }
            for n in nodes
        ],
        'edges': [
            {
                'edge_id': e.edge_id,
                'source_node_id': e.source_node_id,
                'target_node_id': e.target_node_id,
                'source_handle': e.source_handle,
                'target_handle': e.target_handle,
                'label': e.label
            }
            for e in edges
        ]
    }


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    data: WorkflowUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新工作流基本信息"""
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.owner_id == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if data.name is not None:
        workflow.name = data.name
    if data.description is not None:
        workflow.description = data.description
    if data.category is not None:
        workflow.category = data.category
    if data.is_active is not None:
        workflow.is_active = data.is_active
    if data.config_schema is not None:
        workflow.config_schema = data.config_schema
    if data.default_config is not None:
        workflow.default_config = data.default_config
    if data.config is not None:
        workflow.config = data.config

    db.commit()
    db.refresh(workflow)
    
    return workflow


@router.put("/{workflow_id}/canvas", response_model=Dict)
async def save_workflow_canvas(
    workflow_id: int,
    data: WorkflowSaveRequest,
    change_summary: Optional[str] = Query(None, description="版本变更说明"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存工作流画布（节点和边）"""
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.owner_id == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 删除旧的节点和边
    db.query(WorkflowNode).filter(WorkflowNode.workflow_id == workflow_id).delete()
    db.query(WorkflowEdge).filter(WorkflowEdge.workflow_id == workflow_id).delete()
    
    # 准备节点和边的数据用于版本历史
    nodes_data = []
    edges_data = []
    
    # 创建新节点
    for node_data in data.nodes:
        node = WorkflowNode(
            workflow_id=workflow_id,
            node_id=node_data.node_id,
            node_type=node_data.node_type,
            node_subtype=node_data.node_subtype,
            name=node_data.name,
            position_x=node_data.position_x,
            position_y=node_data.position_y,
            config=node_data.config or {}
        )
        db.add(node)
        # 保存到版本历史数据
        nodes_data.append({
            'node_id': node_data.node_id,
            'node_type': node_data.node_type,
            'node_subtype': node_data.node_subtype,
            'name': node_data.name,
            'position_x': node_data.position_x,
            'position_y': node_data.position_y,
            'config': node_data.config or {}
        })
    
    # 创建新边
    for edge_data in data.edges:
        edge = WorkflowEdge(
            workflow_id=workflow_id,
            edge_id=edge_data.edge_id,
            source_node_id=edge_data.source_node_id,
            target_node_id=edge_data.target_node_id,
            source_handle=edge_data.source_handle,
            target_handle=edge_data.target_handle,
            label=edge_data.label
        )
        db.add(edge)
        # 保存到版本历史数据
        edges_data.append({
            'edge_id': edge_data.edge_id,
            'source_node_id': edge_data.source_node_id,
            'target_node_id': edge_data.target_node_id,
            'source_handle': edge_data.source_handle,
            'target_handle': edge_data.target_handle,
            'label': edge_data.label
        })
    
    # 更新版本
    workflow.version += 1
    
    # 创建版本历史记录
    version_record = WorkflowVersion(
        workflow_id=workflow_id,
        version=workflow.version,
        nodes=nodes_data,
        edges=edges_data,
        config=workflow.config,
        change_summary=change_summary,
        created_by=current_user.id
    )
    db.add(version_record)
    
    db.commit()
    
    return {
        'success': True,
        'version': workflow.version,
        'nodes_count': len(data.nodes),
        'edges_count': len(data.edges)
    }


@router.post("/{workflow_id}/execute")
async def execute_user_workflow(
    workflow_id: int,
    data: ExecuteWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行用户工作流"""
    from core.workflow_runtime import WorkflowEngine as RuntimeEngine
    from core.workflow_runtime import WorkflowDefinition, WorkflowNode as RuntimeNode, WorkflowEdge as RuntimeEdge
    from core.workflow_service import (
        GenerateCodeHandler, SendTemplateEmailHandler, ConditionHandler,
        LogHandler, DelayHandler, WebhookHandler, LoopHandler,
        ParallelHandler, SwitchHandler, TransformHandler, EndHandler,
        DataValidateHandler, TriggerHandler
    )
    from datetime import datetime
    
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.owner_id == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 检查工作流是否已发布
    if workflow.status != 'published':
        raise HTTPException(status_code=400, detail="Workflow must be published before execution")
    
    # 获取节点和边
    nodes = db.query(WorkflowNode).filter(
        WorkflowNode.workflow_id == workflow_id
    ).all()
    
    edges = db.query(WorkflowEdge).filter(
        WorkflowEdge.workflow_id == workflow_id
    ).all()
    
    if not nodes:
        raise HTTPException(status_code=400, detail="Workflow has no nodes")
    
    # 转换为运行时格式
    runtime_nodes = {}
    start_node_id = None
    
    for n in nodes:
        node_config = n.config or {}
        
        # 识别起始节点（触发器）
        if n.node_type == 'trigger':
            start_node_id = n.node_id
        
        runtime_nodes[n.node_id] = RuntimeNode(
            id=n.node_id,
            type=n.node_subtype,  # 使用 subtype 作为处理器类型
            label=n.name or n.node_id,
            config=node_config
        )
    
    if not start_node_id:
        raise HTTPException(status_code=400, detail="Workflow has no trigger node")
    
    # 转换边
    runtime_edges = []
    for e in edges:
        runtime_edges.append(RuntimeEdge(
            id=e.edge_id,
            source_node_id=e.source_node_id,
            target_node_id=e.target_node_id,
            source_handle=e.source_handle,
            target_handle=e.target_handle
        ))
        # 向后兼容：设置 next_node_id
        if e.source_node_id in runtime_nodes and not runtime_nodes[e.source_node_id].next_node_id:
            runtime_nodes[e.source_node_id].next_node_id = e.target_node_id
    
    # 创建工作流定义
    definition = WorkflowDefinition(
        id=str(workflow.id),
        name=workflow.name,
        nodes=runtime_nodes,
        start_node_id=start_node_id,
        edges=runtime_edges
    )
    
    # 准备处理器
    handlers = {
        # 触发器
        'trigger_form_submit': TriggerHandler(db).execute,
        'trigger_email_received': TriggerHandler(db).execute,
        'trigger_schedule': TriggerHandler(db).execute,
        'trigger_api': TriggerHandler(db).execute,
        'trigger_manual': TriggerHandler(db).execute,
        'trigger_webhook': TriggerHandler(db).execute,
        # 数据节点
        'data_generate_code': GenerateCodeHandler(db).execute,
        'data_validate': DataValidateHandler(db).execute,
        'data_transform': TransformHandler(db).execute,
        # 动作节点
        'action_send_template': SendTemplateEmailHandler(db).execute,
        'action_send_email': SendTemplateEmailHandler(db).execute,
        # 逻辑节点
        'logic_condition': ConditionHandler(db).execute,
        'logic_delay': DelayHandler(db).execute,
        'logic_switch': SwitchHandler(db).execute,
        'logic_parallel': ParallelHandler(db).execute,
        # 控制流
        'control_delay': DelayHandler(db).execute,
        'control_loop': LoopHandler(db).execute,
        'control_parallel': ParallelHandler(db).execute,
        'control_switch': SwitchHandler(db).execute,
        # 集成节点
        'integration_log': LogHandler(db).execute,
        'integration_webhook': WebhookHandler(db).execute,
        # 结束节点
        'end_success': EndHandler(db).execute,
        'end_failure': EndHandler(db).execute,
    }
    
    # 创建执行记录
    execution = WorkflowExecution(
        workflow_type='custom',
        workflow_id=workflow.id,
        workflow_version=workflow.version,
        user_id=current_user.id,
        trigger_type='manual',
        trigger_data=data.trigger_data,
        status='running',
        started_at=datetime.utcnow()
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    try:
        # 执行工作流
        start_time = datetime.utcnow()
        engine = RuntimeEngine(definition, handlers=handlers)
        final_context = await engine.run(data.trigger_data)
        end_time = datetime.utcnow()
        
        # 计算执行时间
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # 更新执行记录
        execution.status = 'success'
        execution.finished_at = end_time
        execution.result = final_context.data
        
        # 更新工作流执行计数
        workflow.execution_count += 1
        
        db.commit()
        
        return {
            'success': True,
            'execution_id': execution.id,
            'status': 'success',
            'result': final_context.data,
            'error_message': None,
            'nodes_executed': len(final_context.data.get('steps', {})),
            'duration_ms': duration_ms
        }
        
    except Exception as e:
        end_time = datetime.utcnow()
        duration_ms = int((end_time - execution.started_at).total_seconds() * 1000)
        
        # 更新执行记录为失败
        execution.status = 'failed'
        execution.finished_at = end_time
        execution.error_message = str(e)
        db.commit()
        
        return {
            'success': False,
            'execution_id': execution.id,
            'status': 'failed',
            'result': {},
            'error_message': str(e),
            'nodes_executed': 0,
            'duration_ms': duration_ms
        }


@router.post("/{workflow_id}/test")
async def test_user_workflow(
    workflow_id: int,
    data: ExecuteWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试用户工作流（无需发布，用于调试）"""
    from core.workflow_runtime import WorkflowEngine as RuntimeEngine
    from core.workflow_runtime import WorkflowDefinition, WorkflowNode as RuntimeNode, WorkflowEdge as RuntimeEdge
    from core.workflow_service import (
        GenerateCodeHandler, SendTemplateEmailHandler, ConditionHandler,
        LogHandler, DelayHandler, WebhookHandler, LoopHandler,
        ParallelHandler, SwitchHandler, TransformHandler, EndHandler,
        DataValidateHandler, TriggerHandler
    )
    
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.owner_id == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 获取节点和边
    nodes = db.query(WorkflowNode).filter(
        WorkflowNode.workflow_id == workflow_id
    ).all()
    
    edges = db.query(WorkflowEdge).filter(
        WorkflowEdge.workflow_id == workflow_id
    ).all()
    
    if not nodes:
        raise HTTPException(status_code=400, detail="Workflow has no nodes")
    
    # 转换为运行时格式
    runtime_nodes = {}
    start_node_id = None
    
    for n in nodes:
        if n.node_type == 'trigger':
            start_node_id = n.node_id
        
        runtime_nodes[n.node_id] = RuntimeNode(
            id=n.node_id,
            type=n.node_subtype,
            label=n.name or n.node_id,
            config=n.config or {}
        )
    
    if not start_node_id:
        raise HTTPException(status_code=400, detail="Workflow has no trigger node")
    
    # 转换边
    runtime_edges = []
    for e in edges:
        runtime_edges.append(RuntimeEdge(
            id=e.edge_id,
            source_node_id=e.source_node_id,
            target_node_id=e.target_node_id,
            source_handle=e.source_handle,
            target_handle=e.target_handle
        ))
        if e.source_node_id in runtime_nodes and not runtime_nodes[e.source_node_id].next_node_id:
            runtime_nodes[e.source_node_id].next_node_id = e.target_node_id
    
    definition = WorkflowDefinition(
        id=str(workflow.id),
        name=workflow.name,
        nodes=runtime_nodes,
        start_node_id=start_node_id,
        edges=runtime_edges
    )
    
    # 准备处理器（测试模式使用模拟处理器）
    handlers = {
        'trigger_form_submit': TriggerHandler(db).execute,
        'trigger_email_received': TriggerHandler(db).execute,
        'trigger_schedule': TriggerHandler(db).execute,
        'trigger_api': TriggerHandler(db).execute,
        'trigger_manual': TriggerHandler(db).execute,
        'trigger_webhook': TriggerHandler(db).execute,
        'data_generate_code': GenerateCodeHandler(db).execute,
        'data_validate': DataValidateHandler(db).execute,
        'data_transform': TransformHandler(db).execute,
        'action_send_template': SendTemplateEmailHandler(db).execute,
        'action_send_email': SendTemplateEmailHandler(db).execute,
        'logic_condition': ConditionHandler(db).execute,
        'logic_delay': DelayHandler(db).execute,
        'logic_switch': SwitchHandler(db).execute,
        'logic_parallel': ParallelHandler(db).execute,
        'control_delay': DelayHandler(db).execute,
        'control_loop': LoopHandler(db).execute,
        'control_parallel': ParallelHandler(db).execute,
        'control_switch': SwitchHandler(db).execute,
        'integration_log': LogHandler(db).execute,
        'integration_webhook': WebhookHandler(db).execute,
        'end_success': EndHandler(db).execute,
        'end_failure': EndHandler(db).execute,
    }
    
    try:
        from datetime import datetime
        start_time = datetime.utcnow()
        engine = RuntimeEngine(definition, handlers=handlers)
        final_context = await engine.run(data.trigger_data)
        end_time = datetime.utcnow()
        
        # 计算执行时间
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return {
            'success': True,
            'execution_id': 0,  # 测试模式不保存执行记录
            'status': 'success',
            'result': final_context.data,
            'error_message': None,
            'nodes_executed': len(final_context.data.get('steps', {})),
            'duration_ms': duration_ms
        }
        
    except Exception as e:
        return {
            'success': False,
            'execution_id': 0,
            'status': 'failed',
            'result': {},
            'error_message': str(e),
            'nodes_executed': 0,
            'duration_ms': 0
        }


@router.post("/{workflow_id}/publish", response_model=WorkflowResponse)
async def publish_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发布工作流"""
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.owner_id == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 检查是否有节点
    nodes_count = db.query(WorkflowNode).filter(
        WorkflowNode.workflow_id == workflow_id
    ).count()
    
    if nodes_count == 0:
        raise HTTPException(status_code=400, detail="Workflow has no nodes")
    
    workflow.status = 'published'
    workflow.published_version = workflow.version
    workflow.is_active = True
    
    db.commit()
    db.refresh(workflow)
    
    return workflow


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除工作流"""
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.owner_id == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    db.delete(workflow)
    db.commit()
    
    return {'success': True}


# ==================== 版本历史 API ====================

class WorkflowVersionResponse(BaseModel):
    id: int
    workflow_id: int
    version: int
    nodes_count: int
    edges_count: int
    change_summary: Optional[str]
    created_by: Optional[int]
    created_at: Optional[str]
    
    class Config:
        from_attributes = True


@router.get("/{workflow_id}/versions", response_model=List[WorkflowVersionResponse])
async def list_workflow_versions(
    workflow_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流的版本历史列表"""
    # 验证工作流所有权
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.owner_id == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    versions = db.query(WorkflowVersion).filter(
        WorkflowVersion.workflow_id == workflow_id
    ).order_by(WorkflowVersion.version.desc()).limit(limit).all()
    
    return [
        {
            'id': v.id,
            'workflow_id': v.workflow_id,
            'version': v.version,
            'nodes_count': len(v.nodes) if v.nodes else 0,
            'edges_count': len(v.edges) if v.edges else 0,
            'change_summary': v.change_summary,
            'created_by': v.created_by,
            'created_at': v.created_at.isoformat() if v.created_at else None
        }
        for v in versions
    ]


@router.get("/{workflow_id}/versions/{version}", response_model=Dict)
async def get_workflow_version_detail(
    workflow_id: int,
    version: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流特定版本的详细内容"""
    # 验证工作流所有权
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.owner_id == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    version_record = db.query(WorkflowVersion).filter(
        WorkflowVersion.workflow_id == workflow_id,
        WorkflowVersion.version == version
    ).first()
    
    if not version_record:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return {
        'id': version_record.id,
        'workflow_id': version_record.workflow_id,
        'version': version_record.version,
        'nodes': version_record.nodes,
        'edges': version_record.edges,
        'config': version_record.config,
        'change_summary': version_record.change_summary,
        'created_by': version_record.created_by,
        'created_at': version_record.created_at.isoformat() if version_record.created_at else None
    }


@router.post("/{workflow_id}/versions/{version}/restore", response_model=Dict)
async def restore_workflow_version(
    workflow_id: int,
    version: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """恢复工作流到指定版本"""
    # 验证工作流所有权
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.owner_id == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    version_record = db.query(WorkflowVersion).filter(
        WorkflowVersion.workflow_id == workflow_id,
        WorkflowVersion.version == version
    ).first()
    
    if not version_record:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # 删除当前的节点和边
    db.query(WorkflowNode).filter(WorkflowNode.workflow_id == workflow_id).delete()
    db.query(WorkflowEdge).filter(WorkflowEdge.workflow_id == workflow_id).delete()
    
    # 从版本历史恢复节点
    for node_data in version_record.nodes or []:
        node = WorkflowNode(
            workflow_id=workflow_id,
            node_id=node_data.get('node_id'),
            node_type=node_data.get('node_type'),
            node_subtype=node_data.get('node_subtype'),
            name=node_data.get('name'),
            position_x=node_data.get('position_x', 0),
            position_y=node_data.get('position_y', 0),
            config=node_data.get('config', {})
        )
        db.add(node)
    
    # 从版本历史恢复边
    for edge_data in version_record.edges or []:
        edge = WorkflowEdge(
            workflow_id=workflow_id,
            edge_id=edge_data.get('edge_id'),
            source_node_id=edge_data.get('source_node_id'),
            target_node_id=edge_data.get('target_node_id'),
            source_handle=edge_data.get('source_handle'),
            target_handle=edge_data.get('target_handle'),
            label=edge_data.get('label')
        )
        db.add(edge)
    
    # 恢复配置
    if version_record.config:
        workflow.config = version_record.config
    
    # 更新版本号（恢复也算一次新版本）
    workflow.version += 1
    
    # 创建恢复操作的版本记录
    restore_version = WorkflowVersion(
        workflow_id=workflow_id,
        version=workflow.version,
        nodes=version_record.nodes,
        edges=version_record.edges,
        config=version_record.config,
        change_summary=f"恢复到版本 {version}",
        created_by=current_user.id
    )
    db.add(restore_version)
    
    db.commit()
    
    return {
        'success': True,
        'restored_from_version': version,
        'new_version': workflow.version,
        'nodes_count': len(version_record.nodes) if version_record.nodes else 0,
        'edges_count': len(version_record.edges) if version_record.edges else 0
    }