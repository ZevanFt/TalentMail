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
    WorkflowExecution, WorkflowNodeExecution
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
    
    # 更新版本
    workflow.version += 1
    
    db.commit()
    
    return {
        'success': True,
        'version': workflow.version,
        'nodes_count': len(data.nodes),
        'edges_count': len(data.edges)
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