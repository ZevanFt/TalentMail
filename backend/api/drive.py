"""文件中转站 API"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
import os
import uuid
import secrets
import logging

from db.database import get_db
from api.deps import get_current_user
from db.models.user import User
from db.models.drive import DriveFile
from core.security import get_password_hash, verify_password
from utils.rate_limit import SlidingWindowLimiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/drive", tags=["drive"])

# 上传限流：每用户每分钟最多 10 次
_upload_limiter = SlidingWindowLimiter(max_attempts=10, window_seconds=60)

UPLOAD_DIR = "uploads/drive"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 上传安全限制（与 attachments.py 保持一致）
BLOCKED_EXTENSIONS = {
    '.exe', '.sh', '.bat', '.ps1', '.vbs', '.scr', '.cmd',
    '.msi', '.dll', '.com', '.pif', '.cpl', '.hta', '.inf',
    '.html', '.htm', '.svg', '.xhtml',  # 防止 XSS（分享链接直接渲染）
}
BLOCKED_CONTENT_TYPES = {
    'application/x-executable', 'application/x-msdos-program',
    'application/x-msdownload', 'application/x-sh',
    'text/html', 'image/svg+xml', 'application/xhtml+xml',
}


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
    parent_id: Optional[int] = None
    is_folder: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ShareSettings(BaseModel):
    is_public: bool = True
    password: Optional[str] = None
    expires_days: Optional[int] = 7


class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None


class ItemMove(BaseModel):
    target_parent_id: Optional[int] = None  # None = 移到根目录


class ItemRename(BaseModel):
    name: str


@router.get("")
def list_files(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    parent_id: Optional[int] = Query(None, description="父文件夹ID，null表示根目录"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取用户的文件列表（分页，按文件夹层级）"""
    query = db.query(DriveFile).filter(
        DriveFile.user_id == user.id,
        DriveFile.parent_id == parent_id,
    )
    # 文件夹排在前面，再按创建时间降序
    query = query.order_by(DriveFile.is_folder.desc(), DriveFile.created_at.desc())
    total = query.count()
    files = query.offset((page - 1) * limit).limit(limit).all()

    # 面包屑路径
    breadcrumbs = _build_breadcrumbs(db, parent_id, user.id) if parent_id else []

    return {"items": files, "total": total, "breadcrumbs": breadcrumbs}


MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/upload", response_model=DriveFileResponse)
async def upload_file(
    file: UploadFile = File(...),
    parent_id: Optional[int] = Query(None, description="上传到指定文件夹"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """上传文件（最大 50MB）"""
    if not _upload_limiter.allow(f"upload:{user.id}"):
        raise HTTPException(429, "上传过于频繁，请稍后再试")

    # 验证 parent_id（如果指定）
    if parent_id is not None:
        parent = db.query(DriveFile).filter(
            DriveFile.id == parent_id,
            DriveFile.user_id == user.id,
            DriveFile.is_folder == True,
        ).first()
        if not parent:
            raise HTTPException(404, "目标文件夹不存在")

    # 安全检查：扩展名黑名单
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    if ext in BLOCKED_EXTENSIONS:
        raise HTTPException(400, f"不允许上传 {ext} 类型的文件")

    # 安全检查：Content-Type 黑名单
    content_type = (file.content_type or "application/octet-stream").lower()
    if content_type in BLOCKED_CONTENT_TYPES:
        raise HTTPException(400, f"不允许上传 {content_type} 类型的文件")

    # 生成唯一文件名（ext 已在上方安全检查中获取）
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # 流式写入磁盘并检查大小限制（避免整文件加载到内存）
    total_size = 0
    try:
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB 块
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_UPLOAD_SIZE:
                    raise HTTPException(413, f"文件大小超过限制 ({MAX_UPLOAD_SIZE // 1024 // 1024}MB)")
                f.write(chunk)
    except HTTPException:
        # 超出大小限制，清理已写入的文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
    content = None  # 不再持有文件内容引用
    
    # 创建数据库记录
    drive_file = DriveFile(
        user_id=user.id,
        parent_id=parent_id,
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
    file.share_password = get_password_hash(settings.password) if settings.password else None
    if settings.expires_days:
        file.share_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.expires_days)
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
    return {"status": "success", "message": "已取消分享"}


@router.delete("/{file_id}")
def delete_file(file_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """删除文件或文件夹（文件夹递归删除子项）"""
    file = db.query(DriveFile).filter(DriveFile.id == file_id, DriveFile.user_id == user.id).first()
    if not file:
        raise HTTPException(404, "文件不存在")

    # 递归收集所有要删除的项
    items_to_delete = _collect_descendants(db, file_id, user.id)
    items_to_delete.append(file)

    # 删除所有物理文件
    for item in items_to_delete:
        if not item.is_folder and item.storage_path and os.path.exists(item.storage_path):
            os.remove(item.storage_path)

    # 数据库由 CASCADE 自动处理子项，但显式删除更安全
    for item in items_to_delete:
        db.delete(item)
    db.commit()
    return {"status": "success", "message": "删除成功"}


# =============================================================================
# 文件夹操作
# =============================================================================

MAX_FOLDERS_PER_USER = 50
MAX_NESTING_DEPTH = 5


def _get_folder_depth(db: Session, parent_id: Optional[int]) -> int:
    """计算文件夹嵌套深度"""
    depth = 0
    current_id = parent_id
    while current_id is not None:
        folder = db.query(DriveFile).filter(DriveFile.id == current_id).first()
        if not folder:
            break
        current_id = folder.parent_id
        depth += 1
        if depth > MAX_NESTING_DEPTH:
            break
    return depth


def _is_descendant(db: Session, parent_id: int, target_id: int) -> bool:
    """检查 target_id 是否是 parent_id 的后代（防循环引用）"""
    current_id = parent_id
    visited = set()
    while current_id is not None:
        if current_id == target_id:
            return True
        if current_id in visited:
            break
        visited.add(current_id)
        folder = db.query(DriveFile).filter(DriveFile.id == current_id).first()
        if not folder:
            break
        current_id = folder.parent_id
    return False


def _collect_descendants(db: Session, folder_id: int, user_id: int) -> list:
    """递归收集文件夹下所有子项"""
    result = []
    children = db.query(DriveFile).filter(
        DriveFile.parent_id == folder_id,
        DriveFile.user_id == user_id,
    ).all()
    for child in children:
        if child.is_folder:
            result.extend(_collect_descendants(db, child.id, user_id))
        result.append(child)
    return result


def _build_breadcrumbs(db: Session, folder_id: int, user_id: int) -> list:
    """构建面包屑路径（从当前文件夹到根）"""
    crumbs = []
    current_id = folder_id
    visited = set()
    while current_id is not None:
        if current_id in visited:
            break
        visited.add(current_id)
        folder = db.query(DriveFile).filter(
            DriveFile.id == current_id,
            DriveFile.user_id == user_id,
            DriveFile.is_folder == True,
        ).first()
        if not folder:
            break
        crumbs.append({"id": folder.id, "name": folder.original_filename})
        current_id = folder.parent_id
    crumbs.reverse()
    return crumbs


@router.post("/folders", response_model=DriveFileResponse)
def create_folder(
    data: FolderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """创建文件夹（每用户最多 50 个，最多 5 层嵌套）"""
    name = data.name.strip()
    if not name or len(name) > 255:
        raise HTTPException(400, "文件夹名称无效")

    # 限制文件夹总数
    folder_count = db.query(DriveFile).filter(
        DriveFile.user_id == user.id,
        DriveFile.is_folder == True,
    ).count()
    if folder_count >= MAX_FOLDERS_PER_USER:
        raise HTTPException(400, f"文件夹数量已达上限（{MAX_FOLDERS_PER_USER}）")

    # 验证父文件夹
    if data.parent_id is not None:
        parent = db.query(DriveFile).filter(
            DriveFile.id == data.parent_id,
            DriveFile.user_id == user.id,
            DriveFile.is_folder == True,
        ).first()
        if not parent:
            raise HTTPException(404, "父文件夹不存在")
        # 检查嵌套深度
        depth = _get_folder_depth(db, data.parent_id)
        if depth >= MAX_NESTING_DEPTH:
            raise HTTPException(400, f"文件夹嵌套层级已达上限（{MAX_NESTING_DEPTH}层）")

    folder = DriveFile(
        user_id=user.id,
        parent_id=data.parent_id,
        is_folder=True,
        filename=name,
        original_filename=name,
        content_type=None,
        size=0,
        storage_path=None,
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@router.patch("/{item_id}/move", response_model=DriveFileResponse)
def move_item(
    item_id: int,
    data: ItemMove,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """移动文件/文件夹到指定目录"""
    item = db.query(DriveFile).filter(DriveFile.id == item_id, DriveFile.user_id == user.id).first()
    if not item:
        raise HTTPException(404, "文件不存在")

    target_parent_id = data.target_parent_id

    # 不能移动到自身
    if target_parent_id == item_id:
        raise HTTPException(400, "不能将文件夹移动到自身")

    # 验证目标文件夹
    if target_parent_id is not None:
        target = db.query(DriveFile).filter(
            DriveFile.id == target_parent_id,
            DriveFile.user_id == user.id,
            DriveFile.is_folder == True,
        ).first()
        if not target:
            raise HTTPException(404, "目标文件夹不存在")

        # 防循环引用：不能将文件夹移动到自己的子目录下
        if item.is_folder and _is_descendant(db, target_parent_id, item_id):
            raise HTTPException(400, "不能将文件夹移动到自己的子目录")

        # 检查嵌套深度
        depth = _get_folder_depth(db, target_parent_id)
        if depth >= MAX_NESTING_DEPTH:
            raise HTTPException(400, f"目标位置嵌套层级已达上限（{MAX_NESTING_DEPTH}层）")

    item.parent_id = target_parent_id
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}/rename", response_model=DriveFileResponse)
def rename_item(
    item_id: int,
    data: ItemRename,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """重命名文件/文件夹"""
    item = db.query(DriveFile).filter(DriveFile.id == item_id, DriveFile.user_id == user.id).first()
    if not item:
        raise HTTPException(404, "文件不存在")

    name = data.name.strip()
    if not name or len(name) > 255:
        raise HTTPException(400, "名称无效")

    item.original_filename = name
    if item.is_folder:
        item.filename = name
    db.commit()
    db.refresh(item)
    return item


@router.get("/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """下载自己的文件"""
    file = db.query(DriveFile).filter(DriveFile.id == file_id, DriveFile.user_id == user.id).first()
    if not file:
        raise HTTPException(404, "文件不存在")
    
    if not os.path.exists(file.storage_path):
        raise HTTPException(404, "文件已丢失")

    return FileResponse(
        file.storage_path,
        filename=file.original_filename,
        media_type="application/octet-stream",
    )


# 公开分享下载（无需登录）
@router.get("/share/{share_code}")
def get_share_info(share_code: str, password: Optional[str] = None, db: Session = Depends(get_db)):
    """获取分享文件信息"""
    file = db.query(DriveFile).filter(DriveFile.share_code == share_code).first()
    if not file:
        raise HTTPException(404, "分享不存在或已失效")
    
    if file.share_expires_at and file.share_expires_at < datetime.now(timezone.utc):
        raise HTTPException(410, "分享已过期")
    
    # 如果有密码保护，需要验证密码
    if file.share_password:
        if not password:
            raise HTTPException(401, "需要密码")
        if not verify_password(password, file.share_password):
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
    
    if file.share_expires_at and file.share_expires_at < datetime.now(timezone.utc):
        raise HTTPException(410, "分享已过期")
    
    if file.share_password:
        if not password or not verify_password(password, file.share_password):
            raise HTTPException(403, "密码错误")
    
    if not os.path.exists(file.storage_path):
        raise HTTPException(404, "文件已丢失")
    
    # 增加下载计数（原子操作，避免并发丢失）
    db.query(DriveFile).filter(DriveFile.id == file.id).update(
        {DriveFile.download_count: DriveFile.download_count + 1}, synchronize_session=False
    )
    db.commit()

    # 强制附件下载，防止浏览器直接渲染 HTML/SVG 等危险内容
    return FileResponse(
        file.storage_path,
        filename=file.original_filename,
        media_type="application/octet-stream",
    )


# =============================================================================
# 文件预览（安全内联显示）
# =============================================================================

# 安全的可预览 MIME 类型白名单（禁止 SVG — XSS 风险）
PREVIEWABLE_TYPES = {
    # 图片
    'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp', 'image/avif',
    # 文档
    'application/pdf',
    # 文本（会强制以 text/plain 返回，防止 XSS）
    'text/plain', 'text/markdown', 'text/csv',
    # 代码（同样强制 text/plain）
    'application/json', 'application/xml', 'text/xml',
    'text/css', 'text/javascript', 'application/javascript',
}

# 需要强制为 text/plain 的类型（防止浏览器执行脚本/渲染 HTML）
_TEXT_LIKE_TYPES = {
    'text/plain', 'text/markdown', 'text/csv',
    'application/json', 'application/xml', 'text/xml',
    'text/css', 'text/javascript', 'application/javascript',
}


def _is_previewable(content_type: str | None) -> bool:
    """判断文件是否可安全预览"""
    if not content_type:
        return False
    ct = content_type.lower().split(';')[0].strip()
    # 允许所有 image/* 但排除 SVG（XSS 攻击向量）
    if ct.startswith('image/') and ct != 'image/svg+xml':
        return True
    return ct in PREVIEWABLE_TYPES


def _safe_media_type(content_type: str | None) -> str:
    """返回安全的 media_type，文本类型强制为 text/plain"""
    ct = (content_type or '').lower().split(';')[0].strip()
    if ct in _TEXT_LIKE_TYPES:
        return 'text/plain; charset=utf-8'
    return content_type or 'application/octet-stream'


@router.get("/{file_id}/preview")
def preview_file(
    file_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """预览自有文件（安全类型内联显示）"""
    file = db.query(DriveFile).filter(
        DriveFile.id == file_id,
        DriveFile.user_id == user.id,
    ).first()
    if not file:
        raise HTTPException(404, "文件不存在")
    if not os.path.exists(file.storage_path):
        raise HTTPException(404, "文件已丢失")
    if not _is_previewable(file.content_type):
        raise HTTPException(415, "该文件类型不支持预览")

    return FileResponse(
        file.storage_path,
        media_type=_safe_media_type(file.content_type),
        headers={
            "Content-Disposition": f'inline; filename="{file.original_filename}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )


@router.get("/share/{share_code}/preview")
def preview_shared_file(
    share_code: str,
    password: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """预览分享文件（安全类型内联显示）"""
    file = db.query(DriveFile).filter(DriveFile.share_code == share_code).first()
    if not file:
        raise HTTPException(404, "分享不存在或已失效")
    if file.share_expires_at and file.share_expires_at < datetime.now(timezone.utc):
        raise HTTPException(410, "分享已过期")
    if file.share_password:
        if not password or not verify_password(password, file.share_password):
            raise HTTPException(403, "密码错误")
    if not os.path.exists(file.storage_path):
        raise HTTPException(404, "文件已丢失")
    if not _is_previewable(file.content_type):
        raise HTTPException(415, "该文件类型不支持预览")

    return FileResponse(
        file.storage_path,
        media_type=_safe_media_type(file.content_type),
        headers={
            "Content-Disposition": f'inline; filename="{file.original_filename}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )