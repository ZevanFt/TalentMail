from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import logging
from pydantic import BaseModel

from api import deps
from db import models
from db.models.email import Attachment, Email, Folder

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = "/app/uploads/attachments"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 附件安全限制
MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024  # 25MB
CHUNK_SIZE = 8192  # 8KB 流式读取
BLOCKED_EXTENSIONS = {
    '.exe', '.sh', '.bat', '.ps1', '.vbs', '.scr', '.cmd',
    '.msi', '.dll', '.com', '.pif', '.cpl', '.hta', '.inf',
}
BLOCKED_CONTENT_TYPES = {
    'application/x-executable', 'application/x-msdos-program',
    'application/x-msdownload', 'application/x-sh',
}


class AttachmentRead(BaseModel):
    id: int
    filename: str
    content_type: str
    size: int
    email_id: int | None = None

    class Config:
        from_attributes = True


@router.post("/upload", response_model=AttachmentRead)
async def upload_attachment(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """上传附件（先上传，发送邮件时关联）"""
    # 1. 文件扩展名黑名单检查
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    if ext in BLOCKED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不允许上传 {ext} 类型的文件")

    # 2. Content-Type 黑名单检查
    content_type = (file.content_type or "application/octet-stream").lower()
    if content_type in BLOCKED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"不允许上传 {content_type} 类型的文件")

    # 3. 流式写入 + 大小限制检查
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    total_size = 0

    try:
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_ATTACHMENT_SIZE:
                    # 超限：删除已写入的部分文件
                    f.close()
                    os.remove(file_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"文件大小超过限制（最大 {MAX_ATTACHMENT_SIZE // 1024 // 1024}MB）"
                    )
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        # 写入失败时清理
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"附件上传写入失败: {e}")
        raise HTTPException(status_code=500, detail="文件上传失败")

    # 4. 创建数据库记录
    attachment = Attachment(
        user_id=current_user.id,
        filename=file.filename or "unnamed",
        content_type=content_type,
        size=total_size,
        file_path=file_path
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    logger.info(f"附件上传成功: user={current_user.id} file={file.filename} size={total_size}")
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
    
    # 强制作为下载文件返回，防止浏览器内联渲染恶意 HTML/SVG 附件（XSS）
    from starlette.responses import Response
    import mimetypes

    # 仅允许安全的 MIME 类型内联，其他一律 application/octet-stream
    SAFE_INLINE_TYPES = {
        "image/png", "image/jpeg", "image/gif", "image/webp",
        "application/pdf", "text/plain",
    }
    safe_type = attachment.content_type if attachment.content_type in SAFE_INLINE_TYPES else "application/octet-stream"

    return FileResponse(
        attachment.file_path,
        filename=attachment.filename,
        media_type=safe_type,
        headers={
            "Content-Disposition": f'attachment; filename="{attachment.filename}"',
            "X-Content-Type-Options": "nosniff",
        },
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


@router.get("/list")
def list_user_attachments(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """获取用户所有附件（分页）"""
    query = db.query(Attachment).filter(Attachment.user_id == current_user.id).order_by(Attachment.id.desc())
    total = query.count()
    attachments = query.offset((page - 1) * limit).limit(limit).all()
    return {"items": attachments, "total": total}
