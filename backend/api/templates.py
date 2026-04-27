"""
用户写信模板 CRUD API
每用户最多 50 个模板
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from db.database import get_db
from api.deps import get_current_user
from db.models.user import User
from db.models.features import Template

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])

MAX_TEMPLATES_PER_USER = 50


# ── Schemas ──────────────────────────────────────────────────

class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    subject: str = Field(default="", max_length=500)
    body_html: str = Field(default="", max_length=50000)
    body_text: Optional[str] = Field(default=None, max_length=50000)


class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    subject: Optional[str] = Field(default=None, max_length=500)
    body_html: Optional[str] = Field(default=None, max_length=50000)
    body_text: Optional[str] = Field(default=None, max_length=50000)


class TemplateResponse(BaseModel):
    id: int
    name: str | None
    subject: str | None
    body_html: str | None
    body_text: str | None
    created_at: str | None

    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    items: List[TemplateResponse]
    total: int


# ── Endpoints ────────────────────────────────────────────────

@router.get("", response_model=TemplateListResponse)
def list_templates(
    q: str = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """列出当前用户的写信模板"""
    query = db.query(Template).filter(Template.user_id == user.id)
    if q:
        query = query.filter(
            (Template.name.ilike(f"%{q}%")) | (Template.subject.ilike(f"%{q}%"))
        )
    total = query.count()
    items = query.order_by(Template.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return TemplateListResponse(items=items, total=total)


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取单个模板详情"""
    tmpl = db.query(Template).filter(
        Template.id == template_id, Template.user_id == user.id
    ).first()
    if not tmpl:
        raise HTTPException(404, "模板不存在")
    return tmpl


@router.post("", response_model=TemplateResponse, status_code=201)
def create_template(
    data: TemplateCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """创建写信模板（每用户最多 50 个）"""
    count = db.query(Template).filter(Template.user_id == user.id).count()
    if count >= MAX_TEMPLATES_PER_USER:
        raise HTTPException(400, f"模板数量已达上限（{MAX_TEMPLATES_PER_USER} 个）")

    tmpl = Template(
        user_id=user.id,
        name=data.name,
        subject=data.subject,
        body_html=data.body_html,
        body_text=data.body_text,
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    logger.info(f"[Template] 用户 {user.email} 创建模板: {tmpl.name} (id={tmpl.id})")
    return tmpl


@router.put("/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: int,
    data: TemplateUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """更新写信模板"""
    tmpl = db.query(Template).filter(
        Template.id == template_id, Template.user_id == user.id
    ).first()
    if not tmpl:
        raise HTTPException(404, "模板不存在")

    if data.name is not None:
        tmpl.name = data.name
    if data.subject is not None:
        tmpl.subject = data.subject
    if data.body_html is not None:
        tmpl.body_html = data.body_html
    if data.body_text is not None:
        tmpl.body_text = data.body_text

    db.commit()
    db.refresh(tmpl)
    logger.info(f"[Template] 用户 {user.email} 更新模板: {tmpl.name} (id={tmpl.id})")
    return tmpl


@router.delete("/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """删除写信模板"""
    tmpl = db.query(Template).filter(
        Template.id == template_id, Template.user_id == user.id
    ).first()
    if not tmpl:
        raise HTTPException(404, "模板不存在")

    db.delete(tmpl)
    db.commit()
    logger.info(f"[Template] 用户 {user.email} 删除模板: {tmpl.name} (id={template_id})")
    return {"status": "success", "message": "模板已删除"}
