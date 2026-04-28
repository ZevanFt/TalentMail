"""定时邮件发送调度器

每 60 秒扫描一次到期的定时邮件并发送。
"""
import asyncio
import json
import logging
import smtplib
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models.email import Email, Folder, Attachment
from core.mail import send_email as core_send_email
from schemas.email import EmailCreate, EmailRecipient

logger = logging.getLogger(__name__)

# 限制同时发送的定时邮件数量，防止资源耗尽
_send_semaphore = asyncio.Semaphore(5)


async def _send_scheduled_email(email_id: int, sender_email: str):
    """发送单封定时邮件（与 mail.py 的 send_email_task 逻辑一致）"""
    async with _send_semaphore:
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
                # recipients 存储为 JSON: {"to": [{"email":"...", "name":"..."}], "cc": [...]}
                recipients = []
                cc_recipients = []
                if email_obj.recipients:
                    try:
                        r_data = json.loads(email_obj.recipients)
                        for r in r_data.get("to", []):
                            email_addr = r.get("email", "") if isinstance(r, dict) else str(r)
                            if email_addr:
                                recipients.append(EmailRecipient(email=email_addr))
                        for r in r_data.get("cc", []):
                            email_addr = r.get("email", "") if isinstance(r, dict) else str(r)
                            if email_addr:
                                cc_recipients.append(EmailRecipient(email=email_addr))
                    except (json.JSONDecodeError, TypeError):
                        # 兼容旧数据：逗号分隔的纯文本
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
                    cc=cc_recipients or [],
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

        except (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused, smtplib.SMTPDataError) as e:
            # SMTP 5xx = 永久性退信（bounce），不重试
            smtp_code = getattr(e, 'smtp_code', 0) or 0
            is_bounce = smtp_code >= 500
            logger.warning(f"[ScheduledSender] SMTP 错误 {email_id}: code={smtp_code}, {e}")
            try:
                with SessionLocal() as db:
                    email_obj = db.query(Email).filter(Email.id == email_id).first()
                    if email_obj:
                        if is_bounce:
                            email_obj.delivery_status = "bounced"
                            email_obj.delivery_error = f"退信 (SMTP {smtp_code}): {str(e)}"
                            logger.info(f"[ScheduledSender] 邮件退信: {email_id}, SMTP {smtp_code}")
                        else:
                            # 4xx 临时错误，保留重试
                            email_obj.delivery_status = "scheduled"
                            email_obj.delivery_error = f"SMTP 临时错误 ({smtp_code}): {str(e)}"
                        db.commit()
            except Exception:
                logger.error(f"[ScheduledSender] 更新退信状态失败: {email_id}", exc_info=True)

        except Exception as e:
            logger.error(f"[ScheduledSender] 定时邮件发送失败 {email_id}: {e}", exc_info=True)
            try:
                with SessionLocal() as db:
                    email_obj = db.query(Email).filter(Email.id == email_id).first()
                    if email_obj:
                        # 重试逻辑：delivery_error 中记录重试次数，3 次后标 failed
                        retry_count = 0
                        if email_obj.delivery_error and email_obj.delivery_error.startswith("[retry:"):
                            try:
                                retry_count = int(email_obj.delivery_error.split("]")[0].split(":")[1])
                            except (ValueError, IndexError):
                                pass
                        retry_count += 1
                        if retry_count >= 3:
                            email_obj.delivery_status = "failed"
                            email_obj.delivery_error = f"经过 {retry_count} 次重试仍然失败: {str(e)}"
                        else:
                            # 保持 scheduled 状态，下一轮扫描会重试
                            email_obj.delivery_status = "scheduled"
                            email_obj.delivery_error = f"[retry:{retry_count}] {str(e)}"
                        db.commit()
            except Exception:
                logger.error(f"[ScheduledSender] 更新重试状态失败: {email_id}", exc_info=True)


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
