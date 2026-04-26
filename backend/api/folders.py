from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import logging
from api import deps
from db.models import User
from db.models.email import Folder, Email
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()

SYSTEM_ROLES = {"inbox", "sent", "drafts", "trash", "spam", "archive"}
MAX_CUSTOM_FOLDERS = 20


class FolderItem(BaseModel):
    id: int
    name: str
    role: str
    parent_id: Optional[int] = None
    unread_count: int


class FolderListResponse(BaseModel):
    status: str = "success"
    data: List[FolderItem]


class FolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    parent_id: Optional[int] = None


class FolderUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=50)


@router.get("", response_model=FolderListResponse)
def list_folders(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """获取当前用户的文件夹列表"""
    folders = db.query(Folder).filter(Folder.user_id == current_user.id).all()
    folder_ids = [f.id for f in folders]

    # 一次性聚合查询所有文件夹的未读数（替代 N+1 循环）
    unread_counts = {}
    if folder_ids:
        rows = db.query(
            Email.folder_id, func.count(Email.id)
        ).filter(
            Email.folder_id.in_(folder_ids),
            Email.is_read == False,
            Email.is_purged == False
        ).group_by(Email.folder_id).all()
        unread_counts = dict(rows)

    items = [
        FolderItem(
            id=folder.id,
            name=folder.name,
            role=folder.role,
            parent_id=folder.parent_id,
            unread_count=unread_counts.get(folder.id, 0)
        )
        for folder in folders
    ]

    # 按角色排序：系统文件夹在前
    role_order = {"inbox": 0, "sent": 1, "drafts": 2, "trash": 3, "spam": 4, "archive": 5, "user": 6}
    items.sort(key=lambda x: role_order.get(x.role, 99))

    return FolderListResponse(data=items)


@router.post("", response_model=FolderItem)
def create_folder(
    data: FolderCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """创建自定义文件夹"""
    # 检查自定义文件夹数量限制
    custom_count = db.query(func.count(Folder.id)).filter(
        Folder.user_id == current_user.id,
        Folder.role == "user"
    ).scalar() or 0
    if custom_count >= MAX_CUSTOM_FOLDERS:
        raise HTTPException(status_code=400, detail=f"自定义文件夹数量已达上限（{MAX_CUSTOM_FOLDERS}个）")

    # 检查名称是否重复
    existing = db.query(Folder).filter(
        Folder.user_id == current_user.id,
        Folder.name == data.name.strip()
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="文件夹名称已存在")

    # 验证父文件夹 + 嵌套深度限制（最多 3 层）
    MAX_FOLDER_DEPTH = 3
    if data.parent_id:
        parent = db.query(Folder).filter(
            Folder.id == data.parent_id,
            Folder.user_id == current_user.id
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="父文件夹不存在")
        # 计算父文件夹的深度
        depth = 1
        p = parent
        while p.parent_id and depth < MAX_FOLDER_DEPTH + 1:
            p = db.query(Folder).filter(Folder.id == p.parent_id).first()
            if not p:
                break
            depth += 1
        if depth >= MAX_FOLDER_DEPTH:
            raise HTTPException(status_code=400, detail=f"文件夹嵌套不能超过 {MAX_FOLDER_DEPTH} 层")

    folder = Folder(
        user_id=current_user.id,
        name=data.name.strip(),
        role="user",
        parent_id=data.parent_id
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)

    logger.info(f"用户 {current_user.id} 创建文件夹: {folder.name} (id={folder.id})")
    return FolderItem(id=folder.id, name=folder.name, role=folder.role, parent_id=folder.parent_id, unread_count=0)


@router.put("/{folder_id}", response_model=FolderItem)
def update_folder(
    folder_id: int,
    data: FolderUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """重命名文件夹（仅限自定义文件夹）"""
    folder = db.query(Folder).filter(
        Folder.id == folder_id,
        Folder.user_id == current_user.id
    ).first()
    if not folder:
        raise HTTPException(status_code=404, detail="文件夹不存在")

    if folder.role in SYSTEM_ROLES:
        raise HTTPException(status_code=403, detail="系统文件夹不可重命名")

    # 检查名称是否重复
    existing = db.query(Folder).filter(
        Folder.user_id == current_user.id,
        Folder.name == data.name.strip(),
        Folder.id != folder_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="文件夹名称已存在")

    folder.name = data.name.strip()
    db.commit()
    db.refresh(folder)

    # 计算未读数
    unread = db.query(func.count(Email.id)).filter(
        Email.folder_id == folder.id,
        Email.is_read == False,
        Email.is_purged == False
    ).scalar() or 0

    logger.info(f"用户 {current_user.id} 重命名文件夹 {folder_id}: {folder.name}")
    return FolderItem(id=folder.id, name=folder.name, role=folder.role, parent_id=folder.parent_id, unread_count=unread)


@router.delete("/{folder_id}")
def delete_folder(
    folder_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """删除自定义文件夹（邮件移回收件箱）"""
    folder = db.query(Folder).filter(
        Folder.id == folder_id,
        Folder.user_id == current_user.id
    ).first()
    if not folder:
        raise HTTPException(status_code=404, detail="文件夹不存在")

    if folder.role in SYSTEM_ROLES:
        raise HTTPException(status_code=403, detail="系统文件夹不可删除")

    # 获取收件箱
    inbox = db.query(Folder).filter(
        Folder.user_id == current_user.id,
        Folder.role == "inbox"
    ).first()
    if not inbox:
        raise HTTPException(status_code=500, detail="收件箱不存在")

    # 将文件夹内的邮件移到收件箱
    moved_count = db.query(Email).filter(
        Email.folder_id == folder_id
    ).update({Email.folder_id: inbox.id}, synchronize_session=False)

    # 递归处理所有后代文件夹：BFS 遍历，移邮件到收件箱并删除
    pending_ids = [folder_id]
    all_descendant_folders = []
    while pending_ids:
        children = db.query(Folder).filter(
            Folder.parent_id.in_(pending_ids),
            Folder.user_id == current_user.id
        ).all()
        all_descendant_folders.extend(children)
        pending_ids = [c.id for c in children]

    for child in all_descendant_folders:
        db.query(Email).filter(
            Email.folder_id == child.id
        ).update({Email.folder_id: inbox.id}, synchronize_session=False)
        db.delete(child)

    db.delete(folder)
    db.commit()

    logger.info(f"用户 {current_user.id} 删除文件夹 {folder_id}, 移动 {moved_count} 封邮件到收件箱")
    return {"status": "success", "data": {"moved_emails": moved_count}}