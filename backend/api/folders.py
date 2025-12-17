from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from api import deps
from db.models import User
from db.models.email import Folder, Email
from pydantic import BaseModel

router = APIRouter()


class FolderItem(BaseModel):
    id: int
    name: str
    role: str
    unread_count: int


class FolderListResponse(BaseModel):
    status: str = "success"
    data: List[FolderItem]


@router.get("", response_model=FolderListResponse)
def list_folders(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """获取当前用户的文件夹列表"""
    folders = db.query(Folder).filter(Folder.user_id == current_user.id).all()
    
    # 计算每个文件夹的未读数
    items = []
    for folder in folders:
        unread_count = db.query(func.count(Email.id)).filter(
            Email.folder_id == folder.id,
            Email.is_read == False,
            Email.is_purged == False
        ).scalar() or 0
        
        items.append(FolderItem(
            id=folder.id,
            name=folder.name,
            role=folder.role,
            unread_count=unread_count
        ))
    
    # 按角色排序：系统文件夹在前
    role_order = {"inbox": 0, "sent": 1, "drafts": 2, "trash": 3, "spam": 4, "archive": 5, "user": 6}
    items.sort(key=lambda x: role_order.get(x.role, 99))
    
    return FolderListResponse(data=items)