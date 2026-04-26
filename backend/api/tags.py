from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, Field
from db.database import get_db
from api.deps import get_current_user
from db.models.user import User
from db.models.features import Tag, EmailTag
from db.models.email import Email, Folder
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tags", tags=["tags"])


class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$")


class TagUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")


class TagResponse(BaseModel):
    id: int
    name: str
    color: str
    email_count: int = 0

    class Config:
        from_attributes = True


@router.get("")
def get_tags(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 单次查询获取所有标签 + 计数，避免 N+1
    from sqlalchemy import func
    base = db.query(Tag, func.count(EmailTag.id).label("cnt")).outerjoin(
        EmailTag, EmailTag.tag_id == Tag.id
    ).filter(Tag.user_id == user.id).group_by(Tag.id)
    total = db.query(Tag).filter(Tag.user_id == user.id).count()
    rows = base.offset((page - 1) * limit).limit(limit).all()
    items = [TagResponse(id=tag.id, name=tag.name, color=tag.color, email_count=cnt) for tag, cnt in rows]
    return {"items": items, "total": total}


@router.post("", response_model=TagResponse)
def create_tag(data: TagCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    existing = db.query(Tag).filter(Tag.user_id == user.id, Tag.name == data.name).first()
    if existing:
        raise HTTPException(400, "标签名称已存在")
    tag = Tag(user_id=user.id, name=data.name, color=data.color)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    logger.info(f"用户 {user.id} 创建标签: id={tag.id}, name={tag.name}")
    return TagResponse(id=tag.id, name=tag.name, color=tag.color, email_count=0)


@router.put("/{tag_id}", response_model=TagResponse)
def update_tag(tag_id: int, data: TagUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.user_id == user.id).first()
    if not tag:
        raise HTTPException(404, "标签不存在")
    if data.name:
        tag.name = data.name
    if data.color:
        tag.color = data.color
    db.commit()
    count = db.query(EmailTag).filter(EmailTag.tag_id == tag.id).count()
    return TagResponse(id=tag.id, name=tag.name, color=tag.color, email_count=count)


@router.delete("/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.user_id == user.id).first()
    if not tag:
        raise HTTPException(404, "标签不存在")
    tag_name = tag.name
    db.query(EmailTag).filter(EmailTag.tag_id == tag_id).delete()
    db.delete(tag)
    db.commit()
    logger.info(f"用户 {user.id} 删除标签: id={tag_id}, name={tag_name}")
    return {"status": "success", "message": "删除成功"}


@router.post("/email/{email_id}/tag/{tag_id}")
def add_tag_to_email(email_id: int, tag_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.user_id == user.id).first()
    if not tag:
        raise HTTPException(404, "标签不存在")
    # 校验邮件所有权
    user_folders = db.query(Folder.id).filter(Folder.user_id == user.id).subquery()
    email_obj = db.query(Email).filter(Email.id == email_id, Email.folder_id.in_(user_folders)).first()
    if not email_obj:
        raise HTTPException(404, "邮件不存在")
    existing = db.query(EmailTag).filter(EmailTag.email_id == email_id, EmailTag.tag_id == tag_id).first()
    if existing:
        return {"status": "success", "message": "已添加"}
    db.add(EmailTag(email_id=email_id, tag_id=tag_id))
    db.commit()
    return {"status": "success", "message": "添加成功"}


@router.delete("/email/{email_id}/tag/{tag_id}")
def remove_tag_from_email(email_id: int, tag_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # 校验标签和邮件所有权
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.user_id == user.id).first()
    if not tag:
        raise HTTPException(404, "标签不存在")
    user_folders = db.query(Folder.id).filter(Folder.user_id == user.id).subquery()
    email_obj = db.query(Email).filter(Email.id == email_id, Email.folder_id.in_(user_folders)).first()
    if not email_obj:
        raise HTTPException(404, "邮件不存在")
    db.query(EmailTag).filter(EmailTag.email_id == email_id, EmailTag.tag_id == tag_id).delete()
    db.commit()
    return {"status": "success", "message": "移除成功"}


@router.get("/{tag_id}/emails")
def get_emails_by_tag(tag_id: int, page: int = 1, limit: int = 50, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """获取标签下的邮件列表"""
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.user_id == user.id).first()
    if not tag:
        raise HTTPException(404, "标签不存在")
    
    user_folders = db.query(Folder.id).filter(Folder.user_id == user.id).subquery()
    query = db.query(Email).join(EmailTag, Email.id == EmailTag.email_id).filter(
        EmailTag.tag_id == tag_id,
        Email.folder_id.in_(user_folders)
    ).order_by(Email.received_at.desc())
    
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    return {"status": "success", "data": {"items": items, "total": total, "page": page, "limit": limit}}