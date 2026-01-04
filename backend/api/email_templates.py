"""
系统邮件模板管理 API
管理员可以查看、编辑系统邮件模板，配置触发规则，手动发送邮件
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from db.database import get_db
from db.models.system import SystemEmailTemplate
from db.models.template import TemplateMetadata, GlobalVariable
from db.models.automation import AutomationRule
from db.models.user import User
from api.deps import get_current_user
from core.template_engine import TemplateEngine
from core.mail_service import MailService
from core.event_publisher import EventPublisher
from core.config import settings

router = APIRouter()


# ============ Schema ============

class TemplateMetadataResponse(BaseModel):
    """模板元数据响应"""
    code: str
    name: str
    category: str
    description: Optional[str] = None
    trigger_description: Optional[str] = None
    variables: List[dict]
    default_subject: Optional[str] = None
    default_body_html: Optional[str] = None
    default_body_text: Optional[str] = None
    is_system: bool

    class Config:
        from_attributes = True


class GlobalVariableResponse(BaseModel):
    """全局变量响应"""
    id: int
    key: str
    label: str
    value: str
    value_type: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class GlobalVariableUpdate(BaseModel):
    """更新全局变量"""
    value: str


class EmailTemplateBase(BaseModel):
    """邮件模板基础 Schema"""
    name: str
    category: str
    description: Optional[str] = None
    subject: str
    body_html: str
    body_text: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: bool = True


class EmailTemplateCreate(EmailTemplateBase):
    """创建邮件模板"""
    code: str


class EmailTemplateUpdate(BaseModel):
    """更新邮件模板"""
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None


class EmailTemplateResponse(EmailTemplateBase):
    """邮件模板响应"""
    id: int
    code: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class EmailTemplateTest(BaseModel):
    """测试邮件请求"""
    to_email: str
    variables: dict


class EmailTemplateSend(BaseModel):
    """手动发送邮件请求"""
    to: str = Field(..., description="收件人邮箱")
    cc: Optional[str] = Field(None, description="抄送邮箱（可选）")
    variables: Dict[str, Any] = Field(default_factory=dict, description="模板变量")


class TemplateTriggerRuleCreate(BaseModel):
    """创建模板触发规则"""
    trigger_type: str = Field(..., description="触发类型: user_event/scheduled")
    trigger_event: Optional[str] = Field(None, description="系统事件类型，如 user.registered")
    trigger_config: Dict[str, Any] = Field(default_factory=dict, description="触发配置")
    conditions: List[Dict[str, Any]] = Field(default_factory=list, description="触发条件")
    send_to_type: str = Field("trigger_user", description="发送目标: trigger_user/fixed_email/admin")
    send_to_email: Optional[str] = Field(None, description="指定邮箱（send_to_type=fixed_email时使用）")
    cooldown_hours: int = Field(0, description="冷却时间（小时）")
    is_enabled: bool = Field(True, description="是否启用")


class TemplateTriggerRuleResponse(BaseModel):
    """模板触发规则响应"""
    id: int
    name: str
    trigger_type: str
    trigger_config: Dict[str, Any]
    conditions: Optional[List[Dict[str, Any]]]
    actions: List[Dict[str, Any]]
    is_active: bool
    execution_count: int
    created_at: str
    
    class Config:
        from_attributes = True


class EventTypeResponse(BaseModel):
    """事件类型响应"""
    value: str
    label: str
    category: str
    category_label: str
    description: str
    variables: List[str]


# ============ API ============

@router.get("/metadata", response_model=List[TemplateMetadataResponse])
def get_template_metadata(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有模板元数据（仅管理员）
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看模板元数据"
        )
    
    metadata = db.query(TemplateMetadata).order_by(TemplateMetadata.sort_order).all()
    return metadata


@router.get("/metadata/{code}", response_model=TemplateMetadataResponse)
def get_template_metadata_by_code(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个模板元数据（仅管理员）
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看模板元数据"
        )
    
    metadata = db.query(TemplateMetadata).filter(TemplateMetadata.code == code).first()
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板元数据不存在"
        )
    return metadata


@router.get("/global-variables", response_model=List[GlobalVariableResponse])
def get_global_variables(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有全局变量（仅管理员）
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看全局变量"
        )
    
    # 使用 TemplateEngine 获取处理后的变量值（包括动态计算的值）
    engine = TemplateEngine(db)
    processed_vars = engine.get_global_variables()
    
    # 获取数据库中的定义以获取元数据（label, description 等）
    db_vars = db.query(GlobalVariable).filter(GlobalVariable.is_active == True).all()
    
    result = []
    for var in db_vars:
        # 使用处理后的值覆盖数据库中的原始值（对于 dynamic/config 类型）
        current_value = processed_vars.get(var.key, var.value)
        
        result.append(GlobalVariableResponse(
            id=var.id,
            key=var.key,
            label=var.label,
            value=str(current_value),
            value_type=var.value_type,
            description=var.description
        ))
        
    return result


@router.put("/global-variables/{var_id}", response_model=GlobalVariableResponse)
def update_global_variable(
    var_id: int,
    var_data: GlobalVariableUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新全局变量（仅管理员）
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以修改全局变量"
        )
    
    var = db.query(GlobalVariable).filter(GlobalVariable.id == var_id).first()
    if not var:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="全局变量不存在"
        )
    
    # 动态变量不允许修改
    if var.value_type == "dynamic":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="动态变量不允许手动修改"
        )
    
    var.value = var_data.value
    db.commit()
    db.refresh(var)
    
    return GlobalVariableResponse(
        id=var.id,
        key=var.key,
        label=var.label,
        value=var.value,
        value_type=var.value_type,
        description=var.description
    )


@router.get("/", response_model=List[EmailTemplateResponse])
def get_email_templates(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有邮件模板（仅管理员）
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以管理邮件模板"
        )
    
    query = db.query(SystemEmailTemplate)
    
    if category:
        query = query.filter(SystemEmailTemplate.category == category)
    
    templates = query.order_by(SystemEmailTemplate.category, SystemEmailTemplate.name).all()
    
    return [
        EmailTemplateResponse(
            id=t.id,
            code=t.code,
            name=t.name,
            category=t.category,
            description=t.description,
            subject=t.subject,
            body_html=t.body_html,
            body_text=t.body_text,
            variables=t.variables,
            is_active=t.is_active,
            created_at=t.created_at.isoformat() if t.created_at else "",
            updated_at=t.updated_at.isoformat() if t.updated_at else ""
        )
        for t in templates
    ]


@router.get("/{template_id}", response_model=EmailTemplateResponse)
def get_email_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个邮件模板（仅管理员）
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以管理邮件模板"
        )
    
    template = db.query(SystemEmailTemplate).filter(
        SystemEmailTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    return EmailTemplateResponse(
        id=template.id,
        code=template.code,
        name=template.name,
        category=template.category,
        description=template.description,
        subject=template.subject,
        body_html=template.body_html,
        body_text=template.body_text,
        variables=template.variables,
        is_active=template.is_active,
        created_at=template.created_at.isoformat() if template.created_at else "",
        updated_at=template.updated_at.isoformat() if template.updated_at else ""
    )


@router.post("/", response_model=EmailTemplateResponse)
def create_email_template(
    template_data: EmailTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建邮件模板（仅管理员）
    同时创建 template_metadata 记录以保存变量的详细信息
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以管理邮件模板"
        )
    
    # 检查 code 是否已存在
    existing = db.query(SystemEmailTemplate).filter(
        SystemEmailTemplate.code == template_data.code
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"模板代码 '{template_data.code}' 已存在"
        )
    
    # 处理 variables：支持字符串列表和对象列表两种格式
    variables_for_template = []  # 用于 system_email_templates（保存完整对象）
    variables_for_metadata = []  # 用于 template_metadata（保存完整对象）
    
    if template_data.variables:
        for v in template_data.variables:
            if isinstance(v, str):
                # 旧格式：纯字符串
                var_obj = {"key": v, "label": v, "type": "string", "example": "", "required": False}
                variables_for_template.append(var_obj)
                variables_for_metadata.append(var_obj)
            elif isinstance(v, dict):
                # 新格式：完整对象
                var_obj = {
                    "key": v.get("key", ""),
                    "label": v.get("label", v.get("key", "")),
                    "type": v.get("type", "string"),
                    "example": v.get("example", ""),
                    "required": v.get("required", False)
                }
                variables_for_template.append(var_obj)
                variables_for_metadata.append(var_obj)
            else:
                # Pydantic 模型对象
                var_obj = {
                    "key": getattr(v, "key", ""),
                    "label": getattr(v, "label", getattr(v, "key", "")),
                    "type": getattr(v, "type", "string"),
                    "example": getattr(v, "example", "") or "",
                    "required": getattr(v, "required", False)
                }
                variables_for_template.append(var_obj)
                variables_for_metadata.append(var_obj)
    
    # 创建 system_email_templates 记录
    template = SystemEmailTemplate(
        code=template_data.code,
        name=template_data.name,
        category=template_data.category,
        description=template_data.description,
        subject=template_data.subject,
        body_html=template_data.body_html,
        body_text=template_data.body_text,
        variables=variables_for_template,  # 保存完整对象列表
        is_active=template_data.is_active
    )
    
    db.add(template)
    
    # 同时创建/更新 template_metadata 记录
    existing_metadata = db.query(TemplateMetadata).filter(
        TemplateMetadata.code == template_data.code
    ).first()
    
    if existing_metadata:
        # 更新已有的元数据
        existing_metadata.name = template_data.name
        existing_metadata.category = template_data.category
        existing_metadata.description = template_data.description
        existing_metadata.variables = variables_for_metadata
        existing_metadata.default_subject = template_data.subject
        existing_metadata.default_body_html = template_data.body_html
        existing_metadata.default_body_text = template_data.body_text
    else:
        # 创建新的元数据
        metadata = TemplateMetadata(
            code=template_data.code,
            name=template_data.name,
            category=template_data.category,
            description=template_data.description,
            trigger_description=None,  # 用户自定义模板没有触发描述
            variables=variables_for_metadata,
            default_subject=template_data.subject,
            default_body_html=template_data.body_html,
            default_body_text=template_data.body_text,
            is_system=False,  # 用户创建的模板不是系统模板
            sort_order=100  # 排在系统模板后面
        )
        db.add(metadata)
    
    db.commit()
    db.refresh(template)
    
    return EmailTemplateResponse(
        id=template.id,
        code=template.code,
        name=template.name,
        category=template.category,
        description=template.description,
        subject=template.subject,
        body_html=template.body_html,
        body_text=template.body_text,
        variables=template.variables,
        is_active=template.is_active,
        created_at=template.created_at.isoformat() if template.created_at else "",
        updated_at=template.updated_at.isoformat() if template.updated_at else ""
    )


@router.put("/{template_id}", response_model=EmailTemplateResponse)
def update_email_template(
    template_id: int,
    template_data: EmailTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新邮件模板（仅管理员）
    同时更新 template_metadata 记录以保持变量定义同步
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以管理邮件模板"
        )
    
    template = db.query(SystemEmailTemplate).filter(
        SystemEmailTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    # 处理 variables：支持字符串列表和对象列表两种格式
    update_data = template_data.model_dump(exclude_unset=True)
    
    if "variables" in update_data and update_data["variables"] is not None:
        variables_for_template = []
        variables_for_metadata = []
        
        for v in update_data["variables"]:
            if isinstance(v, str):
                # 旧格式：纯字符串
                var_obj = {"key": v, "label": v, "type": "string", "example": "", "required": False}
                variables_for_template.append(var_obj)
                variables_for_metadata.append(var_obj)
            elif isinstance(v, dict):
                # 新格式：完整对象
                var_obj = {
                    "key": v.get("key", ""),
                    "label": v.get("label", v.get("key", "")),
                    "type": v.get("type", "string"),
                    "example": v.get("example", ""),
                    "required": v.get("required", False)
                }
                variables_for_template.append(var_obj)
                variables_for_metadata.append(var_obj)
            else:
                # Pydantic 模型对象
                var_obj = {
                    "key": getattr(v, "key", ""),
                    "label": getattr(v, "label", getattr(v, "key", "")),
                    "type": getattr(v, "type", "string"),
                    "example": getattr(v, "example", "") or "",
                    "required": getattr(v, "required", False)
                }
                variables_for_template.append(var_obj)
                variables_for_metadata.append(var_obj)
        
        update_data["variables"] = variables_for_template
        
        # 同步更新 template_metadata
        metadata = db.query(TemplateMetadata).filter(
            TemplateMetadata.code == template.code
        ).first()
        
        if metadata:
            metadata.variables = variables_for_metadata
            # 同步更新其他相关字段
            if "name" in update_data:
                metadata.name = update_data["name"]
            if "category" in update_data:
                metadata.category = update_data["category"]
            if "description" in update_data:
                metadata.description = update_data["description"]
            if "subject" in update_data:
                metadata.default_subject = update_data["subject"]
            if "body_html" in update_data:
                metadata.default_body_html = update_data["body_html"]
            if "body_text" in update_data:
                metadata.default_body_text = update_data["body_text"]
        else:
            # 如果没有元数据记录，创建一个
            new_metadata = TemplateMetadata(
                code=template.code,
                name=update_data.get("name", template.name),
                category=update_data.get("category", template.category),
                description=update_data.get("description", template.description),
                trigger_description=None,
                variables=variables_for_metadata,
                default_subject=update_data.get("subject", template.subject),
                default_body_html=update_data.get("body_html", template.body_html),
                default_body_text=update_data.get("body_text", template.body_text),
                is_system=False,
                sort_order=100
            )
            db.add(new_metadata)
    
    # 更新模板字段
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    return EmailTemplateResponse(
        id=template.id,
        code=template.code,
        name=template.name,
        category=template.category,
        description=template.description,
        subject=template.subject,
        body_html=template.body_html,
        body_text=template.body_text,
        variables=template.variables,
        is_active=template.is_active,
        created_at=template.created_at.isoformat() if template.created_at else "",
        updated_at=template.updated_at.isoformat() if template.updated_at else ""
    )


@router.delete("/{template_id}")
def delete_email_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除邮件模板（仅管理员）
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以管理邮件模板"
        )
    
    template = db.query(SystemEmailTemplate).filter(
        SystemEmailTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    db.delete(template)
    db.commit()
    
    return {"status": "success", "message": "模板已删除"}


@router.post("/{template_id}/preview")
def preview_email_template(
    template_id: int,
    variables: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    预览邮件模板（仅管理员）
    传入变量，返回渲染后的邮件内容
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以管理邮件模板"
        )
    
    template = db.query(SystemEmailTemplate).filter(
        SystemEmailTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    # 渲染模板
    engine = TemplateEngine(db)
    
    rendered_subject = engine.render(template.subject, variables)
    rendered_body_html = engine.render(template.body_html, variables)
    rendered_body_text = engine.render(template.body_text or "", variables)
    
    return {
        "subject": rendered_subject,
        "body_html": rendered_body_html,
        "body_text": rendered_body_text
    }


@router.post("/{template_id}/test")
def send_test_email(
    template_id: int,
    test_data: EmailTemplateTest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    发送测试邮件（仅管理员）
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以管理邮件模板"
        )
    
    template = db.query(SystemEmailTemplate).filter(
        SystemEmailTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    # 使用 MailService 发送
    mail_service = MailService(db)
    
    # 渲染模板
    engine = TemplateEngine(db)
    rendered_subject = engine.render(template.subject, test_data.variables)
    rendered_body_html = engine.render(template.body_html, test_data.variables)
    rendered_body_text = engine.render(template.body_text or "", test_data.variables)
    
    success = mail_service.send_raw(
        to_email=test_data.to_email,
        subject=rendered_subject,
        body_html=rendered_body_html,
        body_text=rendered_body_text,
        from_email=f"noreply-system@{settings.BASE_DOMAIN}"
    )
    
    if success:
        return {"status": "success", "message": f"测试邮件已发送至 {test_data.to_email}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送失败，请查看服务器日志"
        )


@router.post("/{template_id}/reset", response_model=EmailTemplateResponse)
def reset_template_to_default(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    重置模板为默认值（仅管理员）
    从 TemplateMetadata 中获取默认值并更新模板
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以管理邮件模板"
        )
    
    template = db.query(SystemEmailTemplate).filter(
        SystemEmailTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    # 获取对应的元数据
    metadata = db.query(TemplateMetadata).filter(
        TemplateMetadata.code == template.code
    ).first()
    
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到该模板的默认配置"
        )
    
    # 重置为默认值
    template.subject = metadata.default_subject
    template.body_html = metadata.default_body_html
    template.body_text = metadata.default_body_text
    
    db.commit()
    db.refresh(template)
    
    return EmailTemplateResponse(
        id=template.id,
        code=template.code,
        name=template.name,
        category=template.category,
        description=template.description,
        subject=template.subject,
        body_html=template.body_html,
        body_text=template.body_text,
        variables=template.variables,
        is_active=template.is_active,
        created_at=template.created_at.isoformat() if template.created_at else "",
        updated_at=template.updated_at.isoformat() if template.updated_at else ""
    )


# ============ 手动发送邮件 ============

@router.post("/{template_id}/send")
async def send_template_email(
    template_id: int,
    send_data: EmailTemplateSend,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    使用模板手动发送邮件（仅管理员）
    
    这是为非开发人员设计的功能：
    1. 选择模板
    2. 填写收件人
    3. 填写变量
    4. 一键发送
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以发送模板邮件"
        )
    
    template = db.query(SystemEmailTemplate).filter(
        SystemEmailTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    if not template.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="模板已禁用，无法发送"
        )
    
    # 使用 MailService 发送
    mail_service = MailService(db)
    
    # 渲染模板
    engine = TemplateEngine(db)
    rendered_subject = engine.render(template.subject, send_data.variables)
    rendered_body_html = engine.render(template.body_html, send_data.variables)
    rendered_body_text = engine.render(template.body_text or "", send_data.variables)
    
    # 发送邮件
    # 处理抄送
    cc_list = [send_data.cc] if send_data.cc else None
    
    success = mail_service.send_raw(
        to_email=send_data.to,
        subject=rendered_subject,
        body_html=rendered_body_html,
        body_text=rendered_body_text,
        from_email=f"noreply-system@{settings.BASE_DOMAIN}",
        cc=cc_list
    )
    
    if success:
        return {
            "success": True,
            "message": f"邮件已发送至 {send_data.to}",
            "template_code": template.code,
            "recipient": send_data.to
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送失败，请查看服务器日志"
        )


# ============ 触发规则管理 ============

@router.get("/events/available", response_model=List[EventTypeResponse])
def get_available_events(
    current_user: User = Depends(get_current_user)
):
    """
    获取所有可用的系统事件类型（用于前端显示）
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看事件类型"
        )
    
    events = EventPublisher.get_available_events()
    return [EventTypeResponse(**e) for e in events]


@router.get("/by-code/{template_code}/rules", response_model=List[TemplateTriggerRuleResponse])
def get_template_trigger_rules(
    template_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取某个模板关联的触发规则
    
    触发规则是存储在 automation_rules 表中的记录，
    其 actions 中包含 send_template_email 动作，
    且 template_code 匹配的规则
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看触发规则"
        )
    
    # 验证模板存在
    template = db.query(SystemEmailTemplate).filter(
        SystemEmailTemplate.code == template_code
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    # 查找包含此模板的自动化规则
    # 由于 actions 是 JSON 字段，需要用 JSON 函数查询
    # 这里使用简单方法：查询所有系统规则然后过滤
    rules = db.query(AutomationRule).filter(
        AutomationRule.is_system == True
    ).all()
    
    result = []
    for rule in rules:
        actions = rule.actions or []
        for action in actions:
            if (action.get("type") == "send_template_email" and
                action.get("config", {}).get("template_code") == template_code):
                result.append(TemplateTriggerRuleResponse(
                    id=rule.id,
                    name=rule.name,
                    trigger_type=rule.trigger_type,
                    trigger_config=rule.trigger_config or {},
                    conditions=rule.conditions,
                    actions=rule.actions,
                    is_active=rule.is_active,
                    execution_count=rule.execution_count or 0,
                    created_at=rule.created_at.isoformat() if rule.created_at else ""
                ))
                break
    
    return result


@router.post("/by-code/{template_code}/rules", response_model=TemplateTriggerRuleResponse)
def create_template_trigger_rule(
    template_code: str,
    rule_data: TemplateTriggerRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    为模板创建触发规则
    
    本质是创建一条 AutomationRule，动作为 send_template_email
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以创建触发规则"
        )
    
    # 验证模板存在
    template = db.query(SystemEmailTemplate).filter(
        SystemEmailTemplate.code == template_code
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    # 构建规则名称
    event_label = rule_data.trigger_event or rule_data.trigger_type
    rule_name = f"模板触发: {template.name} - {event_label}"
    
    # 构建 trigger_config
    trigger_config = rule_data.trigger_config.copy()
    if rule_data.trigger_type == "user_event" and rule_data.trigger_event:
        trigger_config["event_type"] = rule_data.trigger_event
    
    # 构建 actions
    actions = [{
        "type": "send_template_email",
        "config": {
            "template_code": template_code,
            "to_type": rule_data.send_to_type,
            "to": rule_data.send_to_email
        }
    }]
    
    # 创建规则
    rule = AutomationRule(
        name=rule_name,
        description=f"自动发送模板 [{template.name}]",
        owner_id=current_user.id,
        is_system=True,  # 标记为系统规则
        is_active=rule_data.is_enabled,
        priority=0,
        trigger_type=rule_data.trigger_type,
        trigger_config=trigger_config,
        conditions=rule_data.conditions,
        actions=actions
    )
    
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return TemplateTriggerRuleResponse(
        id=rule.id,
        name=rule.name,
        trigger_type=rule.trigger_type,
        trigger_config=rule.trigger_config or {},
        conditions=rule.conditions,
        actions=rule.actions,
        is_active=rule.is_active,
        execution_count=rule.execution_count or 0,
        created_at=rule.created_at.isoformat() if rule.created_at else ""
    )


@router.delete("/rules/{rule_id}")
def delete_template_trigger_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除模板触发规则
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以删除触发规则"
        )
    
    rule = db.query(AutomationRule).filter(
        AutomationRule.id == rule_id
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="规则不存在"
        )
    
    db.delete(rule)
    db.commit()
    
    return {"success": True, "message": "规则已删除"}


@router.put("/rules/{rule_id}/toggle")
def toggle_template_trigger_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    启用/禁用模板触发规则
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以修改触发规则"
        )
    
    rule = db.query(AutomationRule).filter(
        AutomationRule.id == rule_id
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="规则不存在"
        )
    
    rule.is_active = not rule.is_active
    db.commit()
    
    return {
        "success": True,
        "is_active": rule.is_active,
        "message": f"规则已{'启用' if rule.is_active else '禁用'}"
    }