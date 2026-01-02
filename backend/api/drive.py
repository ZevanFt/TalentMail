"""文件中转站 API"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
import uuid
import secrets

from db.database import get_db
from api.deps import get_current_user
from db.models.user import User
from db.models.drive import DriveFile

router = APIRouter(prefix="/drive", tags=["drive"])

UPLOAD_DIR = "uploads/drive"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class DriveFileResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    content_type: Optional[str]
    size: int
    share_code: Optional[str]
    is_public: bool
    download_count: int
    share_expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ShareSettings(BaseModel):
    is_public: bool = True
    password: Optional[str] = None
    expires_days: Optional[int] = 7


@router.get("", response_model=List[DriveFileResponse])
def list_files(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """获取用户的文件列表"""
    files = db.query(DriveFile).filter(DriveFile.user_id == user.id).order_by(DriveFile.created_at.desc()).all()
    return files


@router.post("/upload", response_model=DriveFileResponse)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """上传文件"""
    # 生成唯一文件名
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # 保存文件
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 创建数据库记录
    drive_file = DriveFile(
        user_id=user.id,
        filename=unique_filename,
        original_filename=file.filename or "unknown",
        content_type=file.content_type,
        size=len(content),
        storage_path=file_path,
    )
    db.add(drive_file)
    db.commit()
    db.refresh(drive_file)
    return drive_file


@router.post("/{file_id}/share", response_model=DriveFileResponse)
def create_share(file_id: int, settings: ShareSettings, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """创建分享链接"""
    file = db.query(DriveFile).filter(DriveFile.id == file_id, DriveFile.user_id == user.id).first()
    if not file:
        raise HTTPException(404, "文件不存在")
    
    # 生成分享码
    file.share_code = secrets.token_urlsafe(8)
    file.is_public = settings.is_public
    file.share_password = settings.password
    if settings.expires_days:
        file.share_expires_at = datetime.utcnow() + timedelta(days=settings.expires_days)
    else:
        file.share_expires_at = None
    
    db.commit()
    db.refresh(file)
    return file


@router.delete("/{file_id}/share")
def remove_share(file_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """取消分享"""
    file = db.query(DriveFile).filter(DriveFile.id == file_id, DriveFile.user_id == user.id).first()
    if not file:
        raise HTTPException(404, "文件不存在")
    
    file.share_code = None
    file.is_public = False
    file.share_password = None
    file.share_expires_at = None
    db.commit()
    return {"message": "已取消分享"}


@router.delete("/{file_id}")
def delete_file(file_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """删除文件"""
    file = db.query(DriveFile).filter(DriveFile.id == file_id, DriveFile.user_id == user.id).first()
    if not file:
        raise HTTPException(404, "文件不存在")
    
    # 删除物理文件
    if os.path.exists(file.storage_path):
        os.remove(file.storage_path)
    
    db.delete(file)
    db.commit()
    return {"message": "删除成功"}


@router.get("/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """下载自己的文件"""
    file = db.query(DriveFile).filter(DriveFile.id == file_id, DriveFile.user_id == user.id).first()
    if not file:
        raise HTTPException(404, "文件不存在")
    
    if not os.path.exists(file.storage_path):
        raise HTTPException(404, "文件已丢失")
    
    return FileResponse(file.storage_path, filename=file.original_filename, media_type=file.content_type)


# 公开分享下载（无需登录）
@router.get("/share/{share_code}")
def get_share_info(share_code: str, password: Optional[str] = None, db: Session = Depends(get_db)):
    """获取分享文件信息"""
    file = db.query(DriveFile).filter(DriveFile.share_code == share_code).first()
    if not file:
        raise HTTPException(404, "分享不存在或已失效")
    
    if file.share_expires_at and file.share_expires_at < datetime.utcnow():
        raise HTTPException(410, "分享已过期")
    
    # 如果有密码保护，需要验证密码
    if file.share_password:
        if not password:
            raise HTTPException(401, "需要密码")
        if file.share_password != password:
            raise HTTPException(403, "密码错误")
    
    return {
        "original_filename": file.original_filename,
        "size": file.size,
        "content_type": file.content_type,
        "has_password": bool(file.share_password),
        "download_count": file.download_count,
    }


@router.get("/share/{share_code}/download")
def download_shared_file(share_code: str, password: Optional[str] = None, db: Session = Depends(get_db)):
    """下载分享的文件"""
    file = db.query(DriveFile).filter(DriveFile.share_code == share_code).first()
    if not file:
        raise HTTPException(404, "分享不存在或已失效")
    
    if file.share_expires_at and file.share_expires_at < datetime.utcnow():
        raise HTTPException(410, "分享已过期")
    
    if file.share_password and file.share_password != password:
        raise HTTPException(403, "密码错误")
    
    if not os.path.exists(file.storage_path):
        raise HTTPException(404, "文件已丢失")
    
    # 增加下载计数
    file.download_count += 1
    db.commit()
    
    return FileResponse(file.storage_path, filename=file.original_filename, media_type=file.content_type)