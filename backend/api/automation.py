"""
自动化规则 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from db.database import get_db
from db.models.automation import AutomationRule, AutomationLog
from db.models.user import User
from api.deps import get_current_user, get_current_admin_user
from schemas.automation import (
    AutomationRuleCreate,
    AutomationRuleUpdate,
    AutomationRuleResponse,
    AutomationRuleListResponse,
    AutomationLogResponse,
    AutomationLogListResponse,
    ManualTriggerRequest,
    TriggerResponse,
    AutomationMetadataResponse,
    TriggerTypeInfo,
    ConditionOperatorInfo,
    ActionTypeInfo,
)
from core.rule_engine import RuleEngine, TriggerType, ConditionOperator, ActionType

router = APIRouter(prefix="/automation", tags=["automation"])


# ============== 元数据 API ==============

@router.get("/metadata", response_model=AutomationMetadataResponse)
async def get_automation_metadata(
    current_user: User = Depends(get_current_user)
):
    """获取自动化规则元数据（触发器类型、操作符、动作类型等）"""
    
    # 触发器类型
    trigger_types = [
        TriggerTypeInfo(
            type=TriggerType.EMAIL_RECEIVED,
            name="收到邮件",
            description="当收到新邮件时触发",
            config_schema={
                "type": "object",
                "properties": {
                    "folder": {"type": "string", "description": "限定文件夹（可选）"}
                }
            }
        ),
        TriggerTypeInfo(
            type=TriggerType.EMAIL_SENT,
            name="发送邮件",
            description="当发送邮件后触发",
            config_schema={
                "type": "object",
                "properties": {}
            }
        ),
        TriggerTypeInfo(
            type=TriggerType.USER_EVENT,
            name="用户事件",
            description="当用户执行特定操作时触发",
            config_schema={
                "type": "object",
                "properties": {
                    "event_type": {
                        "type": "string",
                        "enum": ["login", "register", "password_change", "*"],
                        "description": "事件类型"
                    }
                },
                "required": ["event_type"]
            }
        ),
        TriggerTypeInfo(
            type=TriggerType.MANUAL,
            name="手动触发",
            description="手动执行规则",
            config_schema={
                "type": "object",
                "properties": {}
            }
        ),
    ]
    
    # 条件操作符
    condition_operators = [
        ConditionOperatorInfo(operator=ConditionOperator.EQUALS, name="等于", description="字段值等于指定值"),
        ConditionOperatorInfo(operator=ConditionOperator.NOT_EQUALS, name="不等于", description="字段值不等于指定值"),
        ConditionOperatorInfo(operator=ConditionOperator.CONTAINS, name="包含", description="字段值包含指定文本"),
        ConditionOperatorInfo(operator=ConditionOperator.NOT_CONTAINS, name="不包含", description="字段值不包含指定文本"),
        ConditionOperatorInfo(operator=ConditionOperator.STARTS_WITH, name="开头是", description="字段值以指定文本开头"),
        ConditionOperatorInfo(operator=ConditionOperator.ENDS_WITH, name="结尾是", description="字段值以指定文本结尾"),
        ConditionOperatorInfo(operator=ConditionOperator.MATCHES_REGEX, name="正则匹配", description="字段值匹配正则表达式"),
        ConditionOperatorInfo(operator=ConditionOperator.GREATER_THAN, name="大于", description="字段值大于指定数值"),
        ConditionOperatorInfo(operator=ConditionOperator.LESS_THAN, name="小于", description="字段值小于指定数值"),
        ConditionOperatorInfo(operator=ConditionOperator.IS_EMPTY, name="为空", description="字段值为空", requires_value=False),
        ConditionOperatorInfo(operator=ConditionOperator.IS_NOT_EMPTY, name="不为空", description="字段值不为空", requires_value=False),
        ConditionOperatorInfo(operator=ConditionOperator.IN_LIST, name="在列表中", description="字段值在指定列表中"),
        ConditionOperatorInfo(operator=ConditionOperator.NOT_IN_LIST, name="不在列表中", description="字段值不在指定列表中"),
    ]
    
    # 动作类型
    action_types = [
        ActionTypeInfo(
            type=ActionType.SEND_EMAIL,
            name="发送邮件",
            description="使用模板发送邮件",
            config_schema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "收件人（支持变量）"},
                    "template_code": {"type": "string", "description": "邮件模板代码"},
                    "variables": {"type": "object", "description": "额外变量"}
                },
                "required": ["to", "template_code"]
            }
        ),
        ActionTypeInfo(
            type=ActionType.FORWARD_EMAIL,
            name="转发邮件",
            description="将邮件转发给指定收件人",
            config_schema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "转发目标（支持变量）"}
                },
                "required": ["to"]
            }
        ),
        ActionTypeInfo(
            type=ActionType.REPLY_EMAIL,
            name="回复邮件",
            description="自动回复邮件",
            config_schema={
                "type": "object",
                "properties": {
                    "body_html": {"type": "string", "description": "HTML 内容（支持变量）"},
                    "body_text": {"type": "string", "description": "纯文本内容（支持变量）"}
                },
                "required": ["body_html"]
            }
        ),
        ActionTypeInfo(
            type=ActionType.ADD_TAG,
            name="添加标签",
            description="为邮件添加标签",
            config_schema={
                "type": "object",
                "properties": {
                    "tag": {"type": "string", "description": "标签名称"}
                },
                "required": ["tag"]
            }
        ),
        ActionTypeInfo(
            type=ActionType.REMOVE_TAG,
            name="移除标签",
            description="移除邮件标签",
            config_schema={
                "type": "object",
                "properties": {
                    "tag": {"type": "string", "description": "标签名称"}
                },
                "required": ["tag"]
            }
        ),
        ActionTypeInfo(
            type=ActionType.MOVE_TO_FOLDER,
            name="移动到文件夹",
            description="将邮件移动到指定文件夹",
            config_schema={
                "type": "object",
                "properties": {
                    "folder": {"type": "string", "description": "文件夹名称"}
                },
                "required": ["folder"]
            }
        ),
        ActionTypeInfo(
            type=ActionType.MARK_AS_READ,
            name="标记已读",
            description="将邮件标记为已读",
            config_schema={"type": "object", "properties": {}}
        ),
        ActionTypeInfo(
            type=ActionType.MARK_AS_STARRED,
            name="标记星标",
            description="将邮件标记为星标",
            config_schema={"type": "object", "properties": {}}
        ),
        ActionTypeInfo(
            type=ActionType.DELETE_EMAIL,
            name="删除邮件",
            description="将邮件移动到垃圾箱",
            config_schema={"type": "object", "properties": {}}
        ),
        ActionTypeInfo(
            type=ActionType.ARCHIVE_EMAIL,
            name="归档邮件",
            description="将邮件移动到归档文件夹",
            config_schema={"type": "object", "properties": {}}
        ),
        ActionTypeInfo(
            type=ActionType.SET_VARIABLE,
            name="设置变量",
            description="设置变量供后续动作使用",
            config_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "变量名"},
                    "value": {"type": "string", "description": "变量值（支持模板）"}
                },
                "required": ["name", "value"]
            }
        ),
        ActionTypeInfo(
            type=ActionType.LOG_MESSAGE,
            name="记录日志",
            description="记录日志消息",
            config_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "日志消息（支持变量）"},
                    "level": {"type": "string", "enum": ["debug", "info", "warning", "error"], "default": "info"}
                },
                "required": ["message"]
            }
        ),
        ActionTypeInfo(
            type=ActionType.WEBHOOK,
            name="调用 Webhook",
            description="发送 HTTP 请求到指定 URL",
            config_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Webhook URL"},
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"], "default": "POST"},
                    "headers": {"type": "object", "description": "请求头"},
                    "body": {"type": "object", "description": "请求体（支持变量）"}
                },
                "required": ["url"]
            }
        ),
    ]
    
    # 可用字段（用于条件匹配）
    available_fields = [
        {"field": "subject", "name": "邮件主题", "type": "string"},
        {"field": "sender_email", "name": "发件人邮箱", "type": "string"},
        {"field": "sender_name", "name": "发件人名称", "type": "string"},
        {"field": "recipient_email", "name": "收件人邮箱", "type": "string"},
        {"field": "body_text", "name": "邮件正文", "type": "string"},
        {"field": "has_attachments", "name": "有附件", "type": "boolean"},
        {"field": "is_read", "name": "已读", "type": "boolean"},
        {"field": "is_starred", "name": "星标", "type": "boolean"},
        {"field": "user_email", "name": "用户邮箱", "type": "string"},
        {"field": "event", "name": "事件类型", "type": "string"},
    ]
    
    return AutomationMetadataResponse(
        trigger_types=trigger_types,
        condition_operators=condition_operators,
        action_types=action_types,
        available_fields=available_fields
    )


# ============== 规则 CRUD API ==============

@router.get("/rules", response_model=AutomationRuleListResponse)
async def list_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    trigger_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的自动化规则列表"""
    query = db.query(AutomationRule).filter(
        (AutomationRule.owner_id == current_user.id) |
        (AutomationRule.is_system == True)
    )
    
    if trigger_type:
        query = query.filter(AutomationRule.trigger_type == trigger_type)
    
    if is_active is not None:
        query = query.filter(AutomationRule.is_active == is_active)
    
    if search:
        query = query.filter(
            AutomationRule.name.ilike(f"%{search}%") |
            AutomationRule.description.ilike(f"%{search}%")
        )
    
    total = query.count()
    
    rules = query.order_by(
        AutomationRule.priority.desc(),
        AutomationRule.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    return AutomationRuleListResponse(
        items=[AutomationRuleResponse.model_validate(r) for r in rules],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/rules", response_model=AutomationRuleResponse)
async def create_rule(
    rule_data: AutomationRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建自动化规则"""
    rule = AutomationRule(
        name=rule_data.name,
        description=rule_data.description,
        owner_id=current_user.id,
        is_system=False,
        is_active=rule_data.is_active,
        priority=rule_data.priority,
        trigger_type=rule_data.trigger_type,
        trigger_config=rule_data.trigger_config,
        conditions=[c.model_dump() for c in rule_data.conditions] if rule_data.conditions else None,
        actions=[a.model_dump() for a in rule_data.actions]
    )
    
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return AutomationRuleResponse.model_validate(rule)


@router.get("/rules/{rule_id}", response_model=AutomationRuleResponse)
async def get_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取规则详情"""
    rule = db.query(AutomationRule).filter(
        AutomationRule.id == rule_id,
        (AutomationRule.owner_id == current_user.id) | (AutomationRule.is_system == True)
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    
    return AutomationRuleResponse.model_validate(rule)


@router.put("/rules/{rule_id}", response_model=AutomationRuleResponse)
async def update_rule(
    rule_id: int,
    rule_data: AutomationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新规则"""
    rule = db.query(AutomationRule).filter(
        AutomationRule.id == rule_id,
        AutomationRule.owner_id == current_user.id  # 只能更新自己的规则
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在或无权限修改")
    
    # 更新字段
    update_data = rule_data.model_dump(exclude_unset=True)
    
    if "conditions" in update_data and update_data["conditions"] is not None:
        update_data["conditions"] = [c.model_dump() if hasattr(c, 'model_dump') else c for c in update_data["conditions"]]
    
    if "actions" in update_data and update_data["actions"] is not None:
        update_data["actions"] = [a.model_dump() if hasattr(a, 'model_dump') else a for a in update_data["actions"]]
    
    for key, value in update_data.items():
        setattr(rule, key, value)
    
    db.commit()
    db.refresh(rule)
    
    return AutomationRuleResponse.model_validate(rule)


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除规则"""
    rule = db.query(AutomationRule).filter(
        AutomationRule.id == rule_id,
        AutomationRule.owner_id == current_user.id  # 只能删除自己的规则
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在或无权限删除")
    
    db.delete(rule)
    db.commit()
    
    return {"message": "规则已删除"}


@router.post("/rules/{rule_id}/toggle")
async def toggle_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """切换规则启用状态"""
    rule = db.query(AutomationRule).filter(
        AutomationRule.id == rule_id,
        AutomationRule.owner_id == current_user.id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在或无权限修改")
    
    rule.is_active = not rule.is_active
    db.commit()
    
    return {"is_active": rule.is_active}


# ============== 规则执行 API ==============

@router.post("/rules/{rule_id}/trigger", response_model=TriggerResponse)
async def trigger_rule(
    rule_id: int,
    request: ManualTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手动触发规则"""
    rule = db.query(AutomationRule).filter(
        AutomationRule.id == rule_id,
        (AutomationRule.owner_id == current_user.id) | (AutomationRule.is_system == True)
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    
    engine = RuleEngine(db)
    
    try:
        log = await engine.trigger_manual(rule_id, request.context, current_user)
        
        return TriggerResponse(
            success=log.status == "success",
            log_id=log.id,
            status=log.status,
            execution_time_ms=log.execution_time_ms or 0,
            actions_executed=log.actions_executed,
            error_message=log.error_message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== 日志 API ==============

@router.get("/logs", response_model=AutomationLogListResponse)
async def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    rule_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取规则执行日志"""
    # 只能查看自己规则的日志
    query = db.query(AutomationLog).join(AutomationRule).filter(
        (AutomationRule.owner_id == current_user.id) |
        (AutomationRule.is_system == True)
    )
    
    if rule_id:
        query = query.filter(AutomationLog.rule_id == rule_id)
    
    if status:
        query = query.filter(AutomationLog.status == status)
    
    total = query.count()
    
    logs = query.order_by(AutomationLog.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    # 添加规则名称
    items = []
    for log in logs:
        log_dict = AutomationLogResponse.model_validate(log).model_dump()
        log_dict["rule_name"] = log.rule.name if log.rule else None
        items.append(AutomationLogResponse(**log_dict))
    
    return AutomationLogListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/logs/{log_id}", response_model=AutomationLogResponse)
async def get_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取日志详情"""
    log = db.query(AutomationLog).join(AutomationRule).filter(
        AutomationLog.id == log_id,
        (AutomationRule.owner_id == current_user.id) | (AutomationRule.is_system == True)
    ).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")
    
    response = AutomationLogResponse.model_validate(log)
    response.rule_name = log.rule.name if log.rule else None
    
    return response


# ============== 管理员 API ==============

@router.get("/admin/rules", response_model=AutomationRuleListResponse)
async def admin_list_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_system: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """管理员获取所有规则"""
    query = db.query(AutomationRule)
    
    if is_system is not None:
        query = query.filter(AutomationRule.is_system == is_system)
    
    total = query.count()
    
    rules = query.order_by(AutomationRule.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    return AutomationRuleListResponse(
        items=[AutomationRuleResponse.model_validate(r) for r in rules],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/admin/rules/system", response_model=AutomationRuleResponse)
async def create_system_rule(
    rule_data: AutomationRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """创建系统规则"""
    rule = AutomationRule(
        name=rule_data.name,
        description=rule_data.description,
        owner_id=None,  # 系统规则没有所有者
        is_system=True,
        is_active=rule_data.is_active,
        priority=rule_data.priority,
        trigger_type=rule_data.trigger_type,
        trigger_config=rule_data.trigger_config,
        conditions=[c.model_dump() for c in rule_data.conditions] if rule_data.conditions else None,
        actions=[a.model_dump() for a in rule_data.actions]
    )
    
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return AutomationRuleResponse.model_validate(rule)