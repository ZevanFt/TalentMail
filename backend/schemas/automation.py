"""
自动化规则相关 Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============== 条件 Schemas ==============

class ConditionSchema(BaseModel):
    """条件配置"""
    field: str = Field(..., description="字段名称")
    operator: str = Field(..., description="操作符")
    value: Optional[Any] = Field(None, description="比较值")


# ============== 动作 Schemas ==============

class ActionSchema(BaseModel):
    """动作配置"""
    type: str = Field(..., description="动作类型")
    config: Dict[str, Any] = Field(default_factory=dict, description="动作配置")


# ============== 规则 Schemas ==============

class AutomationRuleBase(BaseModel):
    """规则基础字段"""
    name: str = Field(..., min_length=1, max_length=100, description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    is_active: bool = Field(True, description="是否启用")
    priority: int = Field(0, description="优先级")
    trigger_type: str = Field(..., description="触发器类型")
    trigger_config: Dict[str, Any] = Field(default_factory=dict, description="触发器配置")
    conditions: Optional[List[ConditionSchema]] = Field(None, description="条件列表")
    actions: List[ActionSchema] = Field(..., min_length=1, description="动作列表")


class AutomationRuleCreate(AutomationRuleBase):
    """创建规则"""
    pass


class AutomationRuleUpdate(BaseModel):
    """更新规则"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    trigger_type: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    conditions: Optional[List[ConditionSchema]] = None
    actions: Optional[List[ActionSchema]] = None


class AutomationRuleResponse(AutomationRuleBase):
    """规则响应"""
    id: int
    owner_id: Optional[int] = None
    is_system: bool = False
    execution_count: int = 0
    last_executed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AutomationRuleListResponse(BaseModel):
    """规则列表响应"""
    items: List[AutomationRuleResponse]
    total: int
    page: int
    page_size: int


# ============== 日志 Schemas ==============

class AutomationLogResponse(BaseModel):
    """日志响应"""
    id: int
    rule_id: int
    trigger_type: str
    trigger_data: Optional[Dict[str, Any]] = None
    conditions_matched: bool
    actions_executed: Optional[List[Dict[str, Any]]] = None
    status: str
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    created_at: datetime
    
    # 关联的规则名称
    rule_name: Optional[str] = None

    class Config:
        from_attributes = True


class AutomationLogListResponse(BaseModel):
    """日志列表响应"""
    items: List[AutomationLogResponse]
    total: int
    page: int
    page_size: int


# ============== 执行 Schemas ==============

class ManualTriggerRequest(BaseModel):
    """手动触发请求"""
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文数据")


class TriggerResponse(BaseModel):
    """触发响应"""
    success: bool
    log_id: int
    status: str
    execution_time_ms: int
    actions_executed: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None


# ============== 元数据 Schemas ==============

class TriggerTypeInfo(BaseModel):
    """触发器类型信息"""
    type: str
    name: str
    description: str
    config_schema: Dict[str, Any]


class ConditionOperatorInfo(BaseModel):
    """条件操作符信息"""
    operator: str
    name: str
    description: str
    requires_value: bool = True


class ActionTypeInfo(BaseModel):
    """动作类型信息"""
    type: str
    name: str
    description: str
    config_schema: Dict[str, Any]


class AutomationMetadataResponse(BaseModel):
    """自动化元数据响应"""
    trigger_types: List[TriggerTypeInfo]
    condition_operators: List[ConditionOperatorInfo]
    action_types: List[ActionTypeInfo]
    available_fields: List[Dict[str, str]]