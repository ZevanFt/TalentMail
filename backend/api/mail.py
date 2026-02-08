from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict
from pydantic import BaseModel
import uuid
import json
import os
from urllib.parse import quote
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr, formatdate
from api import deps
from db.database import SessionLocal
from schemas import email as email_schema
from db import models
from crud import email as email_crud
from core.mail import send_email as core_send_email
from core.mail_sync import sync_user_mailbox, sync_all_mailboxes
from db.models import User
from db.models.email import Email, Folder, Attachment
from db.models.features import TrackingPixel
from crud.folder import get_user_folder_by_role
from core.config import settings
import logging
from datetime import datetime, timezone

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/send", response_model=email_schema.EmailRead)
async def send_email_endpoint(
    email_in: email_schema.EmailCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    logger.info(f"用户 {current_user.email} 请求发送邮件，数据: {email_in.model_dump_json()}")
    try:
        # Get the user's "Sent" folder
        sent_folder = get_user_folder_by_role(db, user_id=current_user.id, role="sent")
        if not sent_folder:
            logger.error(f"用户 {current_user.id} 未找到 'sent' 文件夹。")
            raise HTTPException(status_code=404, detail="Sent folder not found for user.")
        logger.info(f"成功找到用户 {current_user.id} 的 'sent' 文件夹, ID: {sent_folder.id}。")

        # 处理回复关系
        in_reply_to = None
        references = None
        thread_id = None
        
        if email_in.reply_to_id:
            # 查找原邮件
            original_email = db.query(Email).join(Folder).filter(
                Email.id == email_in.reply_to_id,
                Folder.user_id == current_user.id
            ).first()
            if original_email and original_email.message_id:
                in_reply_to = original_email.message_id
                # 构建 references 链
                if original_email.references:
                    references = f"{original_email.references} {original_email.message_id}"
                else:
                    references = original_email.message_id
                # thread_id 使用原邮件的 thread_id，如果没有则使用原邮件的 message_id
                thread_id = original_email.thread_id or original_email.message_id

        # 1. Create the email in the database first
        logger.info("正在调用 crud.create_email...")
        db_email = email_crud.create_email(
            db=db,
            email=email_in,
            sender_email=current_user.email,
            user_id=current_user.id,
            folder_id=sent_folder.id,
            in_reply_to=in_reply_to,
            references=references,
            thread_id=thread_id,
        )
        # 设置初始投递状态
        db_email.delivery_status = "pending"
        db.commit()
        logger.info(f"成功在数据库中创建邮件记录, ID: {db_email.id}。")

        # 1.2 关联附件
        if email_in.attachment_ids:
            db.query(Attachment).filter(
                Attachment.id.in_(email_in.attachment_ids),
                Attachment.user_id == current_user.id,
                Attachment.email_id.is_(None)
            ).update({"email_id": db_email.id}, synchronize_session=False)
            db.commit()

        # 1.5 如果启用追踪，创建追踪像素并插入邮件 HTML
        tracking_pixel_html = ""
        if email_in.is_tracked:
            pixel_id = uuid.uuid4()
            tracking_pixel = TrackingPixel(
                id=pixel_id,
                email_id=db_email.id
            )
            db.add(tracking_pixel)
            db.commit()
            # 生成追踪像素 URL
            base_url = settings.API_BASE_URL.rstrip('/api')
            tracking_url = f"{base_url}/api/track/open/{str(pixel_id)}"
            tracking_pixel_html = f'<img src="{tracking_url}" width="1" height="1" style="display:none" />'
            logger.info(f"已创建追踪像素: {pixel_id}")

        # 2. Add a background task to send the email
        async def send_email_task():
            email_id = db_email.id
            try:
                # 获取附件信息
                attachments_data = []
                with SessionLocal() as db_bg:
                    email_to_update = db_bg.query(models.Email).filter(models.Email.id == email_id).first()
                    if email_to_update:
                        email_to_update.delivery_status = "sending"
                        db_bg.commit()
                    
                    # 查询附件
                    atts = db_bg.query(Attachment).filter(Attachment.email_id == email_id).all()
                    attachments_data = [{"filename": a.filename, "content_type": a.content_type, "file_path": a.file_path} for a in atts]
                
                logger.info(f"后台任务开始: 发送邮件 (DB ID: {email_id})，附件数: {len(attachments_data)}。")
                # 如果有追踪像素，修改邮件内容
                email_to_send = email_in
                if tracking_pixel_html:
                    email_to_send = email_in.model_copy()
                    email_to_send.body_html = (email_in.body_html or "") + tracking_pixel_html
                message_id = await core_send_email(
                    email_data=email_to_send,
                    sender_email=current_user.email,
                    attachments=attachments_data if attachments_data else None,
                )
                # 更新状态为已发送
                with SessionLocal() as db_bg:
                    email_to_update = db_bg.query(models.Email).filter(models.Email.id == email_id).first()
                    if email_to_update:
                        # 移除 message_id 的尖括号，保持与 LMTP 接收时一致
                        clean_message_id = message_id.strip("<>") if message_id else None
                        email_to_update.message_id = clean_message_id
                        email_to_update.delivery_status = "sent"
                        email_to_update.delivery_error = None
                        db_bg.commit()
                        logger.info(f"邮件发送成功，状态已更新为 sent (DB ID: {email_id})。")
            except Exception as e:
                # 更新状态为失败
                with SessionLocal() as db_bg:
                    email_to_update = db_bg.query(models.Email).filter(models.Email.id == email_id).first()
                    if email_to_update:
                        email_to_update.delivery_status = "failed"
                        email_to_update.delivery_error = str(e)
                        db_bg.commit()
                logger.critical(f"后台邮件发送任务发生致命错误 (DB ID: {email_id}): {e}", exc_info=True)


        background_tasks.add_task(send_email_task)
        logger.info(f"邮件发送任务已成功加入后台队列。")

        # 3. Return the initial DB record immediately
        logger.info(f"立即向客户端返回已创建的邮件记录 (ID: {db_email.id})。")
        return db_email

    except Exception as e:
        logger.critical(f"邮件发送端点发生致命错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while sending email.")


@router.post("/sync")
def sync_emails(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """同步当前用户的收件箱邮件（使用 Dovecot Master User）"""
    try:
        new_count = sync_user_mailbox(db, current_user)
        return {"status": "success", "data": {"new_emails": new_count}}
    except Exception as e:
        logger.error(f"同步邮件失败: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync emails")


@router.post("/sync-all")
def sync_all_emails(
    current_user: User = Depends(deps.get_current_active_user),
):
    """同步所有用户的邮件（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    try:
        results = sync_all_mailboxes()
        return {"status": "success", "data": results}
    except Exception as e:
        logger.error(f"同步所有邮件失败: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync all emails")


@router.get("/search", response_model=email_schema.EmailListResponse)
def search_emails(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """搜索邮件（使用 PostgreSQL 全文搜索）"""
    from sqlalchemy import or_, text

    # 获取用户所有文件夹（排除垃圾箱）
    user_folders = db.query(Folder).filter(
        Folder.user_id == current_user.id,
        Folder.role != 'trash'
    ).all()
    folder_ids = [f.id for f in user_folders]

    if not folder_ids:
        return email_schema.EmailListResponse(
            status="success",
            data=email_schema.EmailListData(items=[], total=0, page=page, limit=limit)
        )

    # 使用 PostgreSQL 全文搜索
    # 将搜索词转换为 tsquery 格式（支持多词搜索）
    # 使用 plainto_tsquery 自动处理空格分隔的多个词
    search_query = func.plainto_tsquery('simple', q)

    # 构建查询：使用全文搜索匹配
    query = db.query(Email).filter(
        Email.folder_id.in_(folder_ids),
        Email.is_purged == False,
        Email.search_vector.op('@@')(search_query)
    )

    total = query.count()
    offset = (page - 1) * limit

    # 按相关性排序（ts_rank），然后按时间排序
    emails = query.order_by(
        func.ts_rank(Email.search_vector, search_query).desc(),
        Email.received_at.desc()
    ).offset(offset).limit(limit).all()

    # 批量查询附件数量
    email_ids = [e.id for e in emails]
    attachment_counts: Dict[int, int] = {}
    if email_ids:
        counts = db.query(Attachment.email_id, func.count(Attachment.id)).filter(
            Attachment.email_id.in_(email_ids)
        ).group_by(Attachment.email_id).all()
        attachment_counts = {email_id: count for email_id, count in counts}

    items = []
    for e in emails:
        items.append(email_schema.EmailListItem(
            id=e.id,
            subject=e.subject or "(无主题)",
            sender=e.sender or "",
            snippet=(e.body_text or e.body_html or "")[:100],
            received_at=e.received_at,
            is_read=e.is_read,
            is_starred=e.is_starred,
            has_attachments=attachment_counts.get(e.id, 0) > 0,
            is_tracked=e.is_tracked or False,
            delivery_status=e.delivery_status,
        ))

    return email_schema.EmailListResponse(
        status="success",
        data=email_schema.EmailListData(items=items, total=total, page=page, limit=limit)
    )


@router.get("/snoozed", response_model=email_schema.EmailListResponse)
def list_snoozed_emails(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """获取待办邮件（已设置推迟时间的邮件）"""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    user_folders = db.query(Folder).filter(Folder.user_id == current_user.id).all()
    folder_ids = [f.id for f in user_folders]
    
    query = db.query(Email).filter(
        Email.folder_id.in_(folder_ids),
        Email.is_purged == False,
        Email.snoozed_until.isnot(None),
        Email.snoozed_until > now  # 还未到提醒时间的
    )
    
    total = query.count()
    offset = (page - 1) * limit
    emails = query.order_by(Email.snoozed_until.asc()).offset(offset).limit(limit).all()
    
    # 批量查询附件数量
    email_ids = [e.id for e in emails]
    attachment_counts: Dict[int, int] = {}
    if email_ids:
        counts = db.query(Attachment.email_id, func.count(Attachment.id)).filter(
            Attachment.email_id.in_(email_ids)
        ).group_by(Attachment.email_id).all()
        attachment_counts = {email_id: count for email_id, count in counts}
    
    items = []
    for e in emails:
        items.append(email_schema.EmailListItem(
            id=e.id,
            subject=e.subject or "(无主题)",
            sender=e.sender or "",
            snippet=(e.body_text or e.body_html or "")[:100],
            received_at=e.received_at,
            is_read=e.is_read,
            is_starred=e.is_starred,
            has_attachments=attachment_counts.get(e.id, 0) > 0,
            is_tracked=e.is_tracked or False,
            delivery_status=e.delivery_status,
        ))
    
    return email_schema.EmailListResponse(
        status="success",
        data=email_schema.EmailListData(items=items, total=total, page=page, limit=limit)
    )


@router.get("/all", response_model=email_schema.EmailListResponse)
def list_all_emails(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    is_read: Optional[bool] = None,
    is_starred: Optional[bool] = None,
    inbox_only: bool = Query(False, description="是否只查询收件箱"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """获取所有邮件（跨文件夹）"""
    if inbox_only:
        # 只查询收件箱
        inbox = db.query(Folder).filter(
            Folder.user_id == current_user.id,
            Folder.role == "inbox"
        ).first()
        folder_ids = [inbox.id] if inbox else []
    else:
        # 获取用户所有文件夹ID（排除垃圾箱和垃圾邮件）
        excluded_roles = ['trash', 'spam']
        user_folders = db.query(Folder).filter(
            Folder.user_id == current_user.id,
            ~Folder.role.in_(excluded_roles)
        ).all()
        folder_ids = [f.id for f in user_folders]
    
    query = db.query(Email).filter(
        Email.folder_id.in_(folder_ids),
        Email.is_purged == False
    )
    
    if is_read is not None:
        query = query.filter(Email.is_read == is_read)
    if is_starred is not None:
        query = query.filter(Email.is_starred == is_starred)
    
    total = query.count()
    offset = (page - 1) * limit
    emails = query.order_by(Email.received_at.desc()).offset(offset).limit(limit).all()
    
    # 批量查询附件数量
    email_ids = [e.id for e in emails]
    attachment_counts: Dict[int, int] = {}
    if email_ids:
        counts = db.query(Attachment.email_id, func.count(Attachment.id)).filter(
            Attachment.email_id.in_(email_ids)
        ).group_by(Attachment.email_id).all()
        attachment_counts = {email_id: count for email_id, count in counts}
    
    items = []
    for e in emails:
        items.append(email_schema.EmailListItem(
            id=e.id,
            subject=e.subject or "(无主题)",
            sender=e.sender or "",
            snippet=(e.body_text or e.body_html or "")[:100],
            received_at=e.received_at,
            is_read=e.is_read,
            is_starred=e.is_starred,
            has_attachments=attachment_counts.get(e.id, 0) > 0,
            is_tracked=e.is_tracked or False,
            delivery_status=e.delivery_status,
        ))
    
    return email_schema.EmailListResponse(
        status="success",
        data=email_schema.EmailListData(items=items, total=total, page=page, limit=limit)
    )


@router.get("", response_model=email_schema.EmailListResponse)
def list_emails(
    folder_id: int = Query(..., description="文件夹 ID"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    is_read: Optional[bool] = None,
    is_starred: Optional[bool] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """获取邮件列表"""
    # 验证文件夹属于当前用户
    folder = db.query(Folder).filter(
        Folder.id == folder_id,
        Folder.user_id == current_user.id
    ).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # 构建查询
    query = db.query(Email).filter(
        Email.folder_id == folder_id,
        Email.is_purged == False
    )
    
    if is_read is not None:
        query = query.filter(Email.is_read == is_read)
    if is_starred is not None:
        query = query.filter(Email.is_starred == is_starred)
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * limit
    emails = query.order_by(Email.received_at.desc()).offset(offset).limit(limit).all()
    
    # 批量查询附件数量
    email_ids = [e.id for e in emails]
    attachment_counts: Dict[int, int] = {}
    if email_ids:
        counts = db.query(Attachment.email_id, func.count(Attachment.id)).filter(
            Attachment.email_id.in_(email_ids)
        ).group_by(Attachment.email_id).all()
        attachment_counts = {email_id: count for email_id, count in counts}
    
    # 转换为响应格式
    items = []
    for e in emails:
        items.append(email_schema.EmailListItem(
            id=e.id,
            subject=e.subject or "(无主题)",
            sender=e.sender or "",
            snippet=(e.body_text or e.body_html or "")[:100],
            received_at=e.received_at,
            is_read=e.is_read,
            is_starred=e.is_starred,
            has_attachments=attachment_counts.get(e.id, 0) > 0,
            is_tracked=e.is_tracked or False,
            delivery_status=e.delivery_status,
        ))
    
    return email_schema.EmailListResponse(
        status="success",
        data=email_schema.EmailListData(
            items=items,
            total=total,
            page=page,
            limit=limit
        )
    )


@router.patch("/{email_id}/read")
def mark_email_read(
    email_id: int,
    is_read: bool = Query(..., description="是否已读"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """标记邮件已读/未读"""
    email = db.query(Email).join(Folder).filter(
        Email.id == email_id,
        Folder.user_id == current_user.id
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    email.is_read = is_read
    db.commit()
    
    return {"status": "success", "data": {"id": email_id, "is_read": is_read}}


@router.delete("/{email_id}")
def delete_email(
    email_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """删除邮件（移到垃圾箱）"""
    email = db.query(Email).join(Folder).filter(
        Email.id == email_id,
        Folder.user_id == current_user.id
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # 获取垃圾箱文件夹
    trash_folder = get_user_folder_by_role(db, user_id=current_user.id, role="trash")
    if not trash_folder:
        raise HTTPException(status_code=404, detail="Trash folder not found")
    
    # 移动到垃圾箱
    email.folder_id = trash_folder.id
    from datetime import datetime, timezone
    email.deleted_at = datetime.now(timezone.utc)
    db.commit()
    
    return {"status": "success", "data": {"id": email_id}}


@router.patch("/{email_id}/star")
def mark_email_starred(
    email_id: int,
    is_starred: bool = Query(..., description="是否星标"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """标记邮件星标"""
    email = db.query(Email).join(Folder).filter(
        Email.id == email_id,
        Folder.user_id == current_user.id
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    email.is_starred = is_starred
    db.commit()
    
    return {"status": "success", "data": {"id": email_id, "is_starred": is_starred}}


@router.patch("/{email_id}/snooze")
def snooze_email(
    email_id: int,
    snooze_until: Optional[str] = Query(None, description="推迟到的时间 (ISO 格式)，为空则取消推迟"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """推迟邮件（待办）"""
    email = db.query(Email).join(Folder).filter(
        Email.id == email_id,
        Folder.user_id == current_user.id
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if snooze_until:
        from datetime import datetime
        email.snoozed_until = datetime.fromisoformat(snooze_until.replace('Z', '+00:00'))
    else:
        email.snoozed_until = None
    db.commit()
    
    return {"status": "success", "data": {"id": email_id, "snoozed_until": str(email.snoozed_until) if email.snoozed_until else None}}


@router.post("/{email_id}/resend")
async def resend_email(
    email_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """重新发送失败的邮件"""
    email = db.query(Email).join(Folder).filter(
        Email.id == email_id,
        Folder.user_id == current_user.id
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # 只能重发失败或待发送的邮件
    if email.delivery_status not in ['failed', 'pending']:
        raise HTTPException(status_code=400, detail="只能重新发送失败或待发送的邮件")
    
    # 重置状态
    email.delivery_status = "pending"
    email.delivery_error = None
    db.commit()
    
    # 后台任务重新发送
    async def resend_task():
        try:
            attachments_data = []
            with SessionLocal() as db_bg:
                email_to_send = db_bg.query(models.Email).filter(models.Email.id == email_id).first()
                if not email_to_send:
                    return
                
                email_to_send.delivery_status = "sending"
                db_bg.commit()
                
                # 查询附件
                atts = db_bg.query(Attachment).filter(Attachment.email_id == email_id).all()
                attachments_data = [{"filename": a.filename, "content_type": a.content_type, "file_path": a.file_path} for a in atts]
            
            # 解析收件人
            recipients_data = json.loads(email.recipients)
            to_list = [email_schema.EmailRecipient(email=r['email'], name=r.get('name')) for r in recipients_data.get('to', [])]
            cc_list = [email_schema.EmailRecipient(email=r['email'], name=r.get('name')) for r in recipients_data.get('cc', [])]
            
            email_create = email_schema.EmailCreate(
                to=to_list,
                cc=cc_list,
                bcc=[],
                subject=email.subject or "",
                body_html=email.body_html or "",
                body_text=email.body_text or "",
            )
            
            message_id = await core_send_email(
                email_data=email_create,
                sender_email=email.sender,
                attachments=attachments_data if attachments_data else None,
            )
            
            with SessionLocal() as db_bg:
                email_to_update = db_bg.query(models.Email).filter(models.Email.id == email_id).first()
                if email_to_update:
                    clean_message_id = message_id.strip("<>") if message_id else None
                    email_to_update.message_id = clean_message_id
                    email_to_update.delivery_status = "sent"
                    email_to_update.delivery_error = None
                    db_bg.commit()
                    
        except Exception as e:
            with SessionLocal() as db_bg:
                email_to_update = db_bg.query(models.Email).filter(models.Email.id == email_id).first()
                if email_to_update:
                    email_to_update.delivery_status = "failed"
                    email_to_update.delivery_error = str(e)
                    db_bg.commit()
            logger.error(f"重新发送邮件失败 (ID: {email_id}): {e}")
    
    background_tasks.add_task(resend_task)
    
    return {"status": "success", "data": {"id": email_id, "message": "邮件已加入发送队列"}}


@router.get("/{email_id}", response_model=email_schema.EmailDetailResponse)
def get_email(
    email_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """获取邮件详情"""
    email = db.query(Email).join(Folder).filter(
        Email.id == email_id,
        Folder.user_id == current_user.id
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # 标记为已读
    if not email.is_read:
        email.is_read = True
        db.commit()
    
    # 获取附件
    attachments = db.query(Attachment).filter(Attachment.email_id == email_id).all()
    attachment_list = [
        email_schema.AttachmentInfo(
            id=a.id,
            filename=a.filename or "unnamed",
            content_type=a.content_type or "application/octet-stream",
            size=a.size or 0
        ) for a in attachments
    ]
    
    # 获取标签
    tags_list = []
    if email.tags:
        tags_list = [
            email_schema.TagInfo(
                id=tag.id,
                name=tag.name,
                color=tag.color
            ) for tag in email.tags
        ]
    
    return email_schema.EmailDetailResponse(
        status="success",
        data=email_schema.EmailDetail(
            id=email.id,
            subject=email.subject or "(无主题)",
            sender=email.sender or "",
            recipients=email.recipients or "",
            body_html=email.body_html,
            body_text=email.body_text,
            received_at=email.received_at,
            is_read=email.is_read,
            is_starred=email.is_starred,
            is_tracked=email.is_tracked or False,
            delivery_status=email.delivery_status,
            delivery_error=email.delivery_error,
            attachments=attachment_list,
            tags=tags_list
        )
    )


# --- 草稿 API ---

@router.post("/drafts", response_model=email_schema.DraftResponse)
def save_draft(
    draft: email_schema.DraftCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """保存草稿"""
    drafts_folder = get_user_folder_by_role(db, user_id=current_user.id, role="drafts")
    if not drafts_folder:
        raise HTTPException(status_code=404, detail="Drafts folder not found")
    
    # 构建收件人 JSON
    recipients = {"to": [], "cc": [], "bcc": []}
    if draft.to:
        for email in draft.to.split(","):
            email = email.strip()
            if email:
                recipients["to"].append({"email": email, "name": email.split("@")[0]})
    if draft.cc:
        for email in draft.cc.split(","):
            email = email.strip()
            if email:
                recipients["cc"].append({"email": email, "name": email.split("@")[0]})
    
    db_draft = Email(
        folder_id=drafts_folder.id,
        subject=draft.subject or "",
        sender=current_user.email,
        recipients=json.dumps(recipients),
        body_text=draft.body_text or "",
        body_html=draft.body_html or "",
        is_draft=True,
        is_read=True,
        received_at=datetime.now(timezone.utc),
    )
    db.add(db_draft)
    db.commit()
    db.refresh(db_draft)
    
    return {"status": "success", "data": {"id": db_draft.id}}


@router.put("/drafts/{draft_id}", response_model=email_schema.DraftResponse)
def update_draft(
    draft_id: int,
    draft: email_schema.DraftCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """更新草稿"""
    db_draft = db.query(Email).join(Folder).filter(
        Email.id == draft_id,
        Folder.user_id == current_user.id,
        Email.is_draft == True
    ).first()
    
    if not db_draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # 更新收件人
    recipients = {"to": [], "cc": [], "bcc": []}
    if draft.to:
        for email in draft.to.split(","):
            email = email.strip()
            if email:
                recipients["to"].append({"email": email, "name": email.split("@")[0]})
    if draft.cc:
        for email in draft.cc.split(","):
            email = email.strip()
            if email:
                recipients["cc"].append({"email": email, "name": email.split("@")[0]})
    
    db_draft.subject = draft.subject or ""
    db_draft.recipients = json.dumps(recipients)
    db_draft.body_text = draft.body_text or ""
    db_draft.body_html = draft.body_html or ""
    db.commit()
    
    return {"status": "success", "data": {"id": db_draft.id}}


@router.delete("/drafts/{draft_id}")
def delete_draft(
    draft_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """删除草稿"""
    db_draft = db.query(Email).join(Folder).filter(
        Email.id == draft_id,
        Folder.user_id == current_user.id,
        Email.is_draft == True
    ).first()
    
    if not db_draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    db.delete(db_draft)
    db.commit()
    
    return {"status": "success", "data": {"id": draft_id}}


# --- 批量操作 API ---

class BulkActionRequest(BaseModel):
    """批量操作请求"""
    email_ids: list[int]


class BulkMoveRequest(BulkActionRequest):
    """批量移动请求"""
    folder_id: int


class BulkActionResponse(BaseModel):
    """批量操作响应"""
    status: str
    success_count: int
    failed_count: int
    failed_ids: list[int] = []


@router.post("/bulk/read", response_model=BulkActionResponse)
def bulk_mark_read(
    data: BulkActionRequest,
    is_read: bool = Query(..., description="标记为已读或未读"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """批量标记邮件已读/未读"""
    success_count = 0
    failed_ids = []

    for email_id in data.email_ids:
        email = db.query(Email).join(Folder).filter(
            Email.id == email_id,
            Folder.user_id == current_user.id
        ).first()

        if email:
            email.is_read = is_read
            success_count += 1
        else:
            failed_ids.append(email_id)

    db.commit()

    return BulkActionResponse(
        status="success",
        success_count=success_count,
        failed_count=len(failed_ids),
        failed_ids=failed_ids
    )


@router.post("/bulk/star", response_model=BulkActionResponse)
def bulk_mark_starred(
    data: BulkActionRequest,
    is_starred: bool = Query(..., description="标记为星标或取消星标"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """批量标记邮件星标"""
    success_count = 0
    failed_ids = []

    for email_id in data.email_ids:
        email = db.query(Email).join(Folder).filter(
            Email.id == email_id,
            Folder.user_id == current_user.id
        ).first()

        if email:
            email.is_starred = is_starred
            success_count += 1
        else:
            failed_ids.append(email_id)

    db.commit()

    return BulkActionResponse(
        status="success",
        success_count=success_count,
        failed_count=len(failed_ids),
        failed_ids=failed_ids
    )


@router.post("/bulk/move", response_model=BulkActionResponse)
def bulk_move_emails(
    data: BulkMoveRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """批量移动邮件到指定文件夹"""
    # 验证目标文件夹属于当前用户
    target_folder = db.query(Folder).filter(
        Folder.id == data.folder_id,
        Folder.user_id == current_user.id
    ).first()

    if not target_folder:
        raise HTTPException(status_code=404, detail="目标文件夹不存在")

    success_count = 0
    failed_ids = []

    for email_id in data.email_ids:
        email = db.query(Email).join(Folder).filter(
            Email.id == email_id,
            Folder.user_id == current_user.id
        ).first()

        if email:
            email.folder_id = data.folder_id
            success_count += 1
        else:
            failed_ids.append(email_id)

    db.commit()

    return BulkActionResponse(
        status="success",
        success_count=success_count,
        failed_count=len(failed_ids),
        failed_ids=failed_ids
    )


@router.post("/bulk/delete", response_model=BulkActionResponse)
def bulk_delete_emails(
    data: BulkActionRequest,
    permanent: bool = Query(False, description="是否永久删除（否则移到垃圾箱）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """批量删除邮件"""
    success_count = 0
    failed_ids = []

    if permanent:
        # 永久删除
        for email_id in data.email_ids:
            email = db.query(Email).join(Folder).filter(
                Email.id == email_id,
                Folder.user_id == current_user.id
            ).first()

            if email:
                email.is_purged = True
                success_count += 1
            else:
                failed_ids.append(email_id)
    else:
        # 移到垃圾箱
        trash_folder = get_user_folder_by_role(db, user_id=current_user.id, role="trash")
        if not trash_folder:
            raise HTTPException(status_code=404, detail="垃圾箱文件夹不存在")

        for email_id in data.email_ids:
            email = db.query(Email).join(Folder).filter(
                Email.id == email_id,
                Folder.user_id == current_user.id
            ).first()

            if email:
                email.folder_id = trash_folder.id
                email.deleted_at = datetime.now(timezone.utc)
                success_count += 1
            else:
                failed_ids.append(email_id)

    db.commit()

    return BulkActionResponse(
        status="success",
        success_count=success_count,
        failed_count=len(failed_ids),
        failed_ids=failed_ids
    )


@router.post("/bulk/archive", response_model=BulkActionResponse)
def bulk_archive_emails(
    data: BulkActionRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """批量归档邮件"""
    archive_folder = get_user_folder_by_role(db, user_id=current_user.id, role="archive")
    if not archive_folder:
        raise HTTPException(status_code=404, detail="归档文件夹不存在")

    success_count = 0
    failed_ids = []

    for email_id in data.email_ids:
        email = db.query(Email).join(Folder).filter(
            Email.id == email_id,
            Folder.user_id == current_user.id
        ).first()

        if email:
            email.folder_id = archive_folder.id
            success_count += 1
        else:
            failed_ids.append(email_id)

    db.commit()

    return BulkActionResponse(
        status="success",
        success_count=success_count,
        failed_count=len(failed_ids),
        failed_ids=failed_ids
    )


@router.get("/{email_id}/export")
def export_email(
    email_id: int,
    format: str = Query("eml", description="导出格式：eml 或 pdf"),
    token: str = Query(..., description="认证 token"),
    tz: str = Query("Asia/Shanghai", description="用户时区，如 Asia/Shanghai"),
    db: Session = Depends(deps.get_db),
):
    """导出邮件为 EML 或 PDF 格式（通过 URL token 参数认证）"""
    # 从 token 参数获取用户
    user = deps.get_current_user_from_token(db, token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    email = db.query(Email).join(Folder).filter(
        Email.id == email_id,
        Folder.user_id == user.id
    ).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if format == "eml":
        return export_as_eml(email, db)
    elif format == "pdf":
        return export_as_pdf(email, db, tz)
    else:
        raise HTTPException(status_code=400, detail="不支持的导出格式，请使用 eml 或 pdf")


def export_as_eml(email: Email, db: Session) -> Response:
    """导出邮件为 EML 格式"""
    # 创建 MIME 消息
    if email.body_html:
        msg = MIMEMultipart('alternative')
        # 添加纯文本版本
        if email.body_text:
            text_part = MIMEText(email.body_text, 'plain', 'utf-8')
            msg.attach(text_part)
        # 添加 HTML 版本
        html_part = MIMEText(email.body_html, 'html', 'utf-8')
        msg.attach(html_part)
    else:
        msg = MIMEText(email.body_text or '', 'plain', 'utf-8')
    
    # 设置邮件头
    msg['Subject'] = email.subject or '(无主题)'
    msg['From'] = email.sender or ''
    
    # 解析收件人
    if email.recipients:
        try:
            recipients = json.loads(email.recipients)
            to_list = [r.get('email', '') for r in recipients.get('to', [])]
            cc_list = [r.get('email', '') for r in recipients.get('cc', [])]
            if to_list:
                msg['To'] = ', '.join(to_list)
            if cc_list:
                msg['Cc'] = ', '.join(cc_list)
        except:
            msg['To'] = email.recipients
    
    # 设置日期
    if email.received_at:
        msg['Date'] = formatdate(email.received_at.timestamp(), localtime=True)
    
    # 设置 Message-ID
    if email.message_id:
        msg['Message-ID'] = f'<{email.message_id}>'
    
    # 获取附件
    attachments = db.query(Attachment).filter(Attachment.email_id == email.id).all()
    
    # 如果有附件，需要改用 mixed 类型
    if attachments:
        outer = MIMEMultipart('mixed')
        # 复制头信息
        for key in ['Subject', 'From', 'To', 'Cc', 'Date', 'Message-ID']:
            if msg[key]:
                outer[key] = msg[key]
        outer.attach(msg)
        
        # 添加附件
        for att in attachments:
            if att.file_path and os.path.exists(att.file_path):
                try:
                    with open(att.file_path, 'rb') as f:
                        att_part = MIMEBase('application', 'octet-stream')
                        att_part.set_payload(f.read())
                        encoders.encode_base64(att_part)
                        att_part.add_header(
                            'Content-Disposition',
                            'attachment',
                            filename=att.filename or 'attachment'
                        )
                        outer.attach(att_part)
                except Exception as e:
                    logger.warning(f"无法添加附件 {att.filename}: {e}")
        
        msg = outer
    
    # 生成 EML 内容
    eml_content = msg.as_bytes()
    
    # 生成文件名（使用 RFC 5987 编码支持中文）
    safe_subject = (email.subject or 'email')[:50].replace('/', '_').replace('\\', '_')
    filename = f"{safe_subject}.eml"
    # URL 编码文件名以支持非 ASCII 字符
    encoded_filename = quote(filename, safe='')
    
    return Response(
        content=eml_content,
        media_type="message/rfc822",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


def export_as_pdf(email: Email, db: Session, user_timezone: str = "Asia/Shanghai") -> Response:
    """导出邮件为 PDF 格式（简单 HTML 转 PDF）"""
    from zoneinfo import ZoneInfo
    
    # 获取用户时区
    try:
        user_tz = ZoneInfo(user_timezone)
    except Exception:
        user_tz = ZoneInfo("Asia/Shanghai")  # 默认时区
    
    # 时区显示名称映射
    tz_display_names = {
        "Asia/Shanghai": "北京时间 (UTC+8)",
        "Asia/Tokyo": "东京时间 (UTC+9)",
        "America/New_York": "纽约时间 (UTC-5)",
        "America/Los_Angeles": "洛杉矶时间 (UTC-8)",
        "Europe/London": "伦敦时间 (UTC+0)",
        "Europe/Paris": "巴黎时间 (UTC+1)",
        "UTC": "世界协调时间 (UTC)",
    }
    tz_display = tz_display_names.get(user_timezone, user_timezone)
    
    # 解析收件人
    recipients_str = ""
    if email.recipients:
        try:
            recipients = json.loads(email.recipients)
            to_list = [r.get('email', '') for r in recipients.get('to', [])]
            cc_list = [r.get('email', '') for r in recipients.get('cc', [])]
            if to_list:
                recipients_str += f"收件人: {', '.join(to_list)}"
            if cc_list:
                recipients_str += f"<br>抄送: {', '.join(cc_list)}"
        except:
            recipients_str = f"收件人: {email.recipients}"
    
    # 格式化日期（转换为用户时区）
    date_str = ""
    if email.received_at:
        # 确保时间有时区信息，然后转换为用户时区
        if email.received_at.tzinfo is None:
            from datetime import timezone as dt_timezone
            received_at_utc = email.received_at.replace(tzinfo=dt_timezone.utc)
        else:
            received_at_utc = email.received_at
        received_at_local = received_at_utc.astimezone(user_tz)
        date_str = received_at_local.strftime("%Y年%m月%d日 %H:%M")
    
    # 获取附件列表
    attachments = db.query(Attachment).filter(Attachment.email_id == email.id).all()
    attachments_html = ""
    if attachments:
        att_list = ', '.join([att.filename or 'attachment' for att in attachments])
        attachments_html = f'<p style="color: #666; font-size: 12px; margin-top: 20px; padding-top: 10px; border-top: 1px solid #eee;">📎 附件: {att_list}</p>'
    
    # 构建 HTML 内容
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
            color: #333;
            line-height: 1.6;
        }}
        .header {{
            border-bottom: 2px solid #3b82f6;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .subject {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #1a1a1a;
        }}
        .meta {{
            font-size: 14px;
            color: #666;
        }}
        .meta-row {{
            margin: 5px 0;
        }}
        .label {{
            font-weight: 600;
            color: #444;
        }}
        .body {{
            margin-top: 20px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #999;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="subject">{email.subject or '(无主题)'}</div>
        <div class="meta">
            <div class="meta-row"><span class="label">发件人:</span> {email.sender or ''}</div>
            <div class="meta-row">{recipients_str}</div>
            <div class="meta-row"><span class="label">日期:</span> {date_str}</div>
        </div>
    </div>
    <div class="body">
        {email.body_html or f'<pre style="white-space: pre-wrap; font-family: inherit;">{email.body_text or "(无正文内容)"}</pre>'}
    </div>
    {attachments_html}
    <div class="footer">
        由 TalentMail 导出 · {datetime.now(user_tz).strftime("%Y-%m-%d %H:%M")} ({tz_display})
    </div>
</body>
</html>
"""
    
    # 尝试使用 weasyprint 生成 PDF（如果可用）
    try:
        from weasyprint import HTML
        pdf_content = HTML(string=html_content).write_pdf()
        media_type = "application/pdf"
        ext = "pdf"
    except ImportError:
        # 如果 weasyprint 不可用，返回 HTML 文件
        logger.info("weasyprint 不可用，返回 HTML 格式")
        pdf_content = html_content.encode('utf-8')
        media_type = "text/html"
        ext = "html"
    
    # 生成文件名（使用 RFC 5987 编码支持中文）
    safe_subject = (email.subject or 'email')[:50].replace('/', '_').replace('\\', '_')
    filename = f"{safe_subject}.{ext}"
    # URL 编码文件名以支持非 ASCII 字符
    encoded_filename = quote(filename, safe='')
    
    return Response(
        content=pdf_content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )
