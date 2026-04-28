from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, Field
from db.database import get_db
from api.deps import get_current_user
from db.models.user import User
from db.models.features import Tag, EmailTag
from db.models.email import Email, Folder
from utils.rate_limit import SlidingWindowLimiter
import logging

logger = logging.getLogger(__name__)
_tag_limiter = SlidingWindowLimiter(max_attempts=20, window_seconds=60)

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
    if not _tag_limiter.allow(f"tag_create:{user.id}"):
        raise HTTPException(429, "操作过于频繁，请稍后再试")
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
    if data.name is not None:
        # 重名检查
        dup = db.query(Tag).filter(Tag.user_id == user.id, Tag.name == data.name, Tag.id != tag_id).first()
        if dup:
            raise HTTPException(400, "标签名称已存在")
        tag.name = data.name
    if data.color is not None:
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


class BulkTagRequest(BaseModel):
    """批量标签操作请求"""
    email_ids: list[int] = Field(..., max_length=500)
    tag_id: int


class BulkTagResponse(BaseModel):
    """批量标签操作响应"""
    status: str
    success_count: int
    skipped_count: int


@router.post("/bulk/add", response_model=BulkTagResponse)
def bulk_add_tag(
    data: BulkTagRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """批量给邮件添加标签"""
    tag = db.query(Tag).filter(Tag.id == data.tag_id, Tag.user_id == user.id).first()
    if not tag:
        raise HTTPException(404, "标签不存在")
    # 获取用户拥有的邮件 ID
    user_folder_ids = db.query(Folder.id).filter(Folder.user_id == user.id)
    owned_ids = {
        row[0] for row in db.query(Email.id).filter(
            Email.id.in_(data.email_ids),
            Email.folder_id.in_(user_folder_ids),
        ).all()
    }
    # 查出已有标签关联的邮件
    existing_ids = {
        row[0] for row in db.query(EmailTag.email_id).filter(
            EmailTag.email_id.in_(owned_ids),
            EmailTag.tag_id == data.tag_id,
        ).all()
    }
    to_add = owned_ids - existing_ids
    for eid in to_add:
        db.add(EmailTag(email_id=eid, tag_id=data.tag_id))
    db.commit()
    logger.info(f"用户 {user.id} 批量添加标签 {tag.name}: {len(to_add)} 封邮件")
    return BulkTagResponse(status="success", success_count=len(to_add), skipped_count=len(existing_ids))


@router.post("/bulk/remove", response_model=BulkTagResponse)
def bulk_remove_tag(
    data: BulkTagRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """批量移除邮件标签"""
    tag = db.query(Tag).filter(Tag.id == data.tag_id, Tag.user_id == user.id).first()
    if not tag:
        raise HTTPException(404, "标签不存在")
    user_folder_ids = db.query(Folder.id).filter(Folder.user_id == user.id)
    owned_ids = {
        row[0] for row in db.query(Email.id).filter(
            Email.id.in_(data.email_ids),
            Email.folder_id.in_(user_folder_ids),
        ).all()
    }
    removed = db.query(EmailTag).filter(
        EmailTag.email_id.in_(owned_ids),
        EmailTag.tag_id == data.tag_id,
    ).delete(synchronize_session=False)
    db.commit()
    logger.info(f"用户 {user.id} 批量移除标签 {tag.name}: {removed} 封邮件")
    return BulkTagResponse(status="success", success_count=removed, skipped_count=len(owned_ids) - removed)


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
def get_emails_by_tag(tag_id: int, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
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