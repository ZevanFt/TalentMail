"""定时邮件发送调度器

每 60 秒扫描一次到期的定时邮件并发送。
"""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models.email import Email, Folder, Attachment
from core.mail import send_email as core_send_email
from schemas.email import EmailCreate, EmailRecipient

logger = logging.getLogger(__name__)


async def _send_scheduled_email(email_id: int, sender_email: str):
    """发送单封定时邮件（与 mail.py 的 send_email_task 逻辑一致）"""
    try:
        with SessionLocal() as db:
            email_obj = db.query(Email).filter(Email.id == email_id).first()
            if not email_obj:
                logger.error(f"[ScheduledSender] 邮件不存在: {email_id}")
                return

            # 更新为发送中
            email_obj.delivery_status = "sending"
            db.commit()

            # 获取附件
            atts = db.query(Attachment).filter(Attachment.email_id == email_id).all()
            attachments_data = [
                {"filename": a.filename, "content_type": a.content_type, "file_path": a.file_path}
                for a in atts
            ] if atts else None

            # 构造 EmailCreate 用于发送
            recipients = []
            if email_obj.recipients:
                # recipients 存的是简单文本，按逗号分割
                for addr in email_obj.recipients.split(","):
                    addr = addr.strip()
                    if addr:
                        recipients.append(EmailRecipient(email=addr))

            if not recipients:
                email_obj.delivery_status = "failed"
                email_obj.delivery_error = "收件人为空"
                db.commit()
                return

            email_data = EmailCreate(
                to=recipients,
                subject=email_obj.subject or "",
                body_html=email_obj.body_html or "",
                body_text=email_obj.body_text or None,
            )

            message_id = await core_send_email(
                email_data=email_data,
                sender_email=sender_email,
                attachments=attachments_data,
            )

            # 更新为已发送
            email_obj.message_id = message_id.strip("<>") if message_id else None
            email_obj.delivery_status = "sent"
            email_obj.delivery_error = None
            email_obj.sent_at = datetime.now(timezone.utc)
            email_obj.scheduled_send_at = None  # 清除定时标记
            db.commit()
            logger.info(f"[ScheduledSender] 定时邮件发送成功: {email_id}")

    except Exception as e:
        logger.error(f"[ScheduledSender] 定时邮件发送失败 {email_id}: {e}", exc_info=True)
        try:
            with SessionLocal() as db:
                email_obj = db.query(Email).filter(Email.id == email_id).first()
                if email_obj:
                    email_obj.delivery_status = "failed"
                    email_obj.delivery_error = str(e)
                    db.commit()
        except Exception:
            pass


async def check_scheduled_emails(interval: int = 60):
    """定时邮件检查任务（默认 60 秒间隔）"""
    logger.info(f"[ScheduledSender] 定时邮件调度器已启动，检查间隔: {interval}s")
    while True:
        await asyncio.sleep(interval)
        try:
            db = SessionLocal()
            try:
                now = datetime.now(timezone.utc)
                pending = db.query(Email).join(Folder).filter(
                    Email.scheduled_send_at.isnot(None),
                    Email.scheduled_send_at <= now,
                    Email.delivery_status == "scheduled"
                ).all()

                if not pending:
                    continue

                logger.info(f"[ScheduledSender] 发现 {len(pending)} 封到期定时邮件")

                for email_obj in pending:
                    # 获取发件人邮箱
                    from db.models.user import User
                    folder = db.query(Folder).filter(Folder.id == email_obj.folder_id).first()
                    if not folder:
                        continue
                    user = db.query(User).filter(User.id == folder.user_id).first()
                    if not user:
                        continue

                    # 异步发送，不阻塞循环
                    asyncio.create_task(_send_scheduled_email(email_obj.id, user.email))

            finally:
                db.close()

        except Exception as e:
            logger.error(f"[ScheduledSender] 检查定时邮件失败: {e}", exc_info=True)
