from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import Optional
from api import deps
from db.database import SessionLocal
from schemas import email as email_schema
from db import models
from crud import email as email_crud
from core.mail import send_email as core_send_email
from core.mail_sync import sync_user_mailbox, sync_all_mailboxes
from db.models import User
from db.models.email import Email, Folder
from crud.folder import get_user_folder_by_role
import logging

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

        # 1. Create the email in the database first
        logger.info("正在调用 crud.create_email...")
        db_email = email_crud.create_email(
            db=db,
            email=email_in,
            sender_email=current_user.email,
            user_id=current_user.id,
            folder_id=sent_folder.id,
        )
        logger.info(f"成功在数据库中创建邮件记录, ID: {db_email.id}。")

        # 2. Add a background task to send the email
        async def send_email_task():
            try:
                logger.info(f"后台任务开始: 发送邮件 (DB ID: {db_email.id})。")
                message_id = await core_send_email(
                    email_data=email_in,
                    sender_email=current_user.email,
                )
                if message_id:
                    # We need a new DB session for the background task
                    with SessionLocal() as db_bg:
                        # Re-fetch the object in the new session before updating
                        email_to_update = db_bg.query(models.Email).filter(models.Email.id == db_email.id).first()
                        if email_to_update:
                            email_to_update.message_id = message_id
                            db_bg.commit()
                            logger.info(f"邮件发送成功，已更新 Message-ID: {message_id} (DB ID: {db_email.id})。")
                        else:
                            logger.error(f"后台任务错误: 在更新 Message-ID 时未找到邮件记录 (DB ID: {db_email.id})。")
                else:
                    logger.error(f"核心邮件发送函数 core_send_email 未返回 Message-ID (DB ID: {db_email.id})。")
            except Exception as e:
                logger.critical(f"后台邮件发送任务发生致命错误 (DB ID: {db_email.id}): {e}", exc_info=True)


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
            has_attachments=False,  # TODO: 实现附件检测
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
            attachments=[]  # TODO: 实现附件
        )
    )
