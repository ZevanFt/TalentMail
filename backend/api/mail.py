from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import json
from api import deps
from db.database import SessionLocal
from schemas import email as email_schema
from db import models
from crud import email as email_crud
from core.mail import send_email as core_send_email
from core.mail_sync import sync_user_mailbox, sync_all_mailboxes
from db.models import User
from db.models.email import Email, Folder
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
                # 更新状态为发送中
                with SessionLocal() as db_bg:
                    email_to_update = db_bg.query(models.Email).filter(models.Email.id == email_id).first()
                    if email_to_update:
                        email_to_update.delivery_status = "sending"
                        db_bg.commit()
                
                logger.info(f"后台任务开始: 发送邮件 (DB ID: {email_id})。")
                # 如果有追踪像素，修改邮件内容
                email_to_send = email_in
                if tracking_pixel_html:
                    email_to_send = email_in.model_copy()
                    email_to_send.body_html = (email_in.body_html or "") + tracking_pixel_html
                message_id = await core_send_email(
                    email_data=email_to_send,
                    sender_email=current_user.email,
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
    """搜索邮件（主题、发件人、正文）"""
    from sqlalchemy import or_
    
    # 获取用户所有文件夹（排除垃圾箱）
    user_folders = db.query(Folder).filter(
        Folder.user_id == current_user.id,
        Folder.role != 'trash'
    ).all()
    folder_ids = [f.id for f in user_folders]
    
    # 搜索条件：主题、发件人、正文包含关键词
    search_pattern = f"%{q}%"
    query = db.query(Email).filter(
        Email.folder_id.in_(folder_ids),
        Email.is_purged == False,
        or_(
            Email.subject.ilike(search_pattern),
            Email.sender.ilike(search_pattern),
            Email.body_text.ilike(search_pattern),
            Email.body_html.ilike(search_pattern)
        )
    )
    
    total = query.count()
    offset = (page - 1) * limit
    emails = query.order_by(Email.received_at.desc()).offset(offset).limit(limit).all()
    
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
            has_attachments=False,
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
            has_attachments=False,
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
            has_attachments=False,
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
            has_attachments=False,
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
            with SessionLocal() as db_bg:
                email_to_send = db_bg.query(models.Email).filter(models.Email.id == email_id).first()
                if not email_to_send:
                    return
                
                email_to_send.delivery_status = "sending"
                db_bg.commit()
            
            # 解析收件人
            import json
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
            attachments=[]
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
