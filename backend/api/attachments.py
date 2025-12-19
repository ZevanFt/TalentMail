from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from pydantic import BaseModel

from api import deps
from db import models
from db.models.email import Attachment, Email, Folder

router = APIRouter()

UPLOAD_DIR = "/app/uploads/attachments"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class AttachmentRead(BaseModel):
    id: int
    filename: str
    content_type: str
    size: int

    class Config:
        from_attributes = True


@router.post("/upload", response_model=AttachmentRead)
async def upload_attachment(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """上传附件（先上传，发送邮件时关联）"""
    # 生成唯一文件名
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    
    # 保存文件
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 创建数据库记录
    attachment = Attachment(
        user_id=current_user.id,
        filename=file.filename or "unnamed",
        content_type=file.content_type or "application/octet-stream",
        size=len(content),
        file_path=file_path
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    
    return attachment


@router.get("/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """下载附件"""
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    
    # 验证权限：用户上传的或邮件属于用户
    if attachment.user_id != current_user.id:
        if attachment.email_id:
            email = db.query(Email).join(Folder).filter(
                Email.id == attachment.email_id,
                Folder.user_id == current_user.id
            ).first()
            if not email:
                raise HTTPException(status_code=403, detail="无权访问")
        else:
            raise HTTPException(status_code=403, detail="无权访问")
    
    if not attachment.file_path or not os.path.exists(attachment.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        attachment.file_path,
        filename=attachment.filename,
        media_type=attachment.content_type
    )


@router.delete("/{attachment_id}")
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """删除未关联的附件"""
    attachment = db.query(Attachment).filter(
        Attachment.id == attachment_id,
        Attachment.user_id == current_user.id,
        Attachment.email_id.is_(None)  # 只能删除未关联邮件的
    ).first()
    
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在或无法删除")
    
    # 删除文件
    if attachment.file_path and os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)
    
    db.delete(attachment)
    db.commit()
    
    return {"status": "success"}


@router.get("/email/{email_id}", response_model=List[AttachmentRead])
def get_email_attachments(
    email_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取邮件的附件列表"""
    # 验证邮件属于用户
    email = db.query(Email).join(Folder).filter(
        Email.id == email_id,
        Folder.user_id == current_user.id
    ).first()
    if not email:
        raise HTTPException(status_code=404, detail="邮件不存在")
    
    attachments = db.query(Attachment).filter(Attachment.email_id == email_id).all()
    return attachments
