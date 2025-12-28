from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from db.database import get_db
from api.deps import get_current_user
from db.models.user import User
from db.models.features import Tag, EmailTag
from db.models.email import Email, Folder

router = APIRouter(prefix="/tags", tags=["tags"])


class TagCreate(BaseModel):
    name: str
    color: str = "#3B82F6"


class TagUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


class TagResponse(BaseModel):
    id: int
    name: str
    color: str
    email_count: int = 0

    class Config:
        from_attributes = True


@router.get("", response_model=List[TagResponse])
def get_tags(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    tags = db.query(Tag).filter(Tag.user_id == user.id).all()
    result = []
    for tag in tags:
        count = db.query(EmailTag).filter(EmailTag.tag_id == tag.id).count()
        result.append(TagResponse(id=tag.id, name=tag.name, color=tag.color, email_count=count))
    return result


@router.post("", response_model=TagResponse)
def create_tag(data: TagCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    existing = db.query(Tag).filter(Tag.user_id == user.id, Tag.name == data.name).first()
    if existing:
        raise HTTPException(400, "标签名称已存在")
    tag = Tag(user_id=user.id, name=data.name, color=data.color)
    db.add(tag)
    db.commit()
    db.refresh(tag)
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
    db.query(EmailTag).filter(EmailTag.tag_id == tag_id).delete()
    db.delete(tag)
    db.commit()
    return {"message": "删除成功"}


@router.post("/email/{email_id}/tag/{tag_id}")
def add_tag_to_email(email_id: int, tag_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.user_id == user.id).first()
    if not tag:
        raise HTTPException(404, "标签不存在")
    existing = db.query(EmailTag).filter(EmailTag.email_id == email_id, EmailTag.tag_id == tag_id).first()
    if existing:
        return {"message": "已添加"}
    db.add(EmailTag(email_id=email_id, tag_id=tag_id))
    db.commit()
    return {"message": "添加成功"}


@router.delete("/email/{email_id}/tag/{tag_id}")
def remove_tag_from_email(email_id: int, tag_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.query(EmailTag).filter(EmailTag.email_id == email_id, EmailTag.tag_id == tag_id).delete()
    db.commit()
    return {"message": "移除成功"}


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
    return {"items": items, "total": total}