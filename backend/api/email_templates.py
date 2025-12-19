"""
系统邮件模板管理 API
管理员可以查看、编辑系统邮件模板
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db.database import get_db
from db.models.system import SystemEmailTemplate
from db.models.user import User
from api.deps import get_current_user

router = APIRouter()


# ============ Schema ============

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


# ============ API ============

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
    
    template = SystemEmailTemplate(
        code=template_data.code,
        name=template_data.name,
        category=template_data.category,
        description=template_data.description,
        subject=template_data.subject,
        body_html=template_data.body_html,
        body_text=template_data.body_text,
        variables=template_data.variables,
        is_active=template_data.is_active
    )
    
    db.add(template)
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
    
    # 更新字段
    update_data = template_data.model_dump(exclude_unset=True)
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
    from core.mail import render_template
    
    rendered_subject = render_template(template.subject, variables)
    rendered_body_html = render_template(template.body_html, variables)
    rendered_body_text = render_template(template.body_text or "", variables)
    
    return {
        "subject": rendered_subject,
        "body_html": rendered_body_html,
        "body_text": rendered_body_text
    }