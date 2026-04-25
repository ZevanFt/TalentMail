"""邮件同步服务 - 使用 Dovecot Master 用户从 IMAP 同步邮件到数据库

同步范围：
  1. 所有注册用户 (User) 的邮箱
  2. 所有活跃的临时邮箱 (TempMailbox)
"""
import imaplib
import email
import hashlib
import asyncio
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models.user import User
from db.models.email import Email, Folder, TempMailbox
from core.config import settings
from core.email_parser import decode_mime_header, parse_email_date, get_email_body

# 模块级事件队列：同步过程中收集新邮件元数据，由 periodic_sync 异步触发工作流
_pending_email_events: list = []

logger = logging.getLogger(__name__)

# Dovecot Master 用户配置
MASTER_USER = settings.MAIL_MASTER_USER
MASTER_PASSWORD = settings.MAIL_MASTER_PASSWORD or settings.ADMIN_PASSWORD


def _connect_imap() -> imaplib.IMAP4:
    """建立 IMAP 连接（根据配置选择 SSL 或 STARTTLS）"""
    if settings.MAIL_USE_SSL:
        imap = imaplib.IMAP4_SSL(settings.MAIL_SERVER, 993)
    else:
        imap = imaplib.IMAP4(settings.MAIL_SERVER, 143)
        try:
            imap.starttls()
        except Exception:
            pass
    return imap


def _sync_imap_inbox(
    db: Session,
    imap_email: str,
    folder_id: int,
    mailbox_address: str,
    user_id: Optional[int] = None,
) -> int:
    """通用 IMAP 同步：从 imap_email 的 INBOX 同步到指定 folder，标记为 mailbox_address。

    Args:
        db: 数据库会话
        imap_email: IMAP 登录的邮箱地址（用 master user 登录）
        folder_id: 目标文件夹 ID（存入哪个 folder）
        mailbox_address: 邮件的 mailbox_address 字段（用于 Pool API 查询）

    Returns:
        同步的邮件数量
    """
    synced = 0
    imap = None
    try:
        imap = _connect_imap()
        login_user = f"{imap_email}*{MASTER_USER}"
        imap.login(login_user, MASTER_PASSWORD)

        # 获取已有的 message_id（按 mailbox_address 去重）
        existing_ids = set(
            row[0] for row in db.query(Email.message_id).filter(
                Email.folder_id == folder_id,
                Email.mailbox_address == mailbox_address,
                Email.message_id.isnot(None)
            ).all()
        )

        status, _ = imap.select('INBOX', readonly=True)
        if status != "OK":
            return 0

        _, data = imap.search(None, 'ALL')
        email_ids = data[0].split()

        for eid in email_ids:
            _, msg_data = imap.fetch(eid, '(RFC822)')
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            msg_id = msg.get("Message-ID", "")
            if msg_id:
                msg_id = msg_id.strip("<>")
            else:
                msg_id = hashlib.sha256(raw_email).hexdigest()[:64]

            if msg_id in existing_ids:
                continue

            body_text, body_html = get_email_body(msg)

            # 提取线程信息
            in_reply_to_raw = msg.get("In-Reply-To", "")
            if in_reply_to_raw:
                in_reply_to_raw = in_reply_to_raw.strip().strip("<>")
            references_raw = msg.get("References", "")
            thread_id = None
            if in_reply_to_raw:
                parent = db.query(Email.thread_id, Email.message_id).filter(
                    Email.message_id == in_reply_to_raw
                ).first()
                if parent and parent.thread_id:
                    thread_id = parent.thread_id
                else:
                    thread_id = in_reply_to_raw

            # 黑名单检查：被拦截的邮件投入 spam 文件夹
            target_folder_id = folder_id
            if user_id:
                try:
                    from api.spam import is_sender_blocked
                    sender_raw = decode_mime_header(msg.get("From", ""))
                    sender_addr = sender_raw
                    if '<' in sender_addr and '>' in sender_addr:
                        sender_addr = sender_addr.split('<')[1].split('>')[0].strip().lower()
                    if sender_addr and is_sender_blocked(db, user_id, sender_addr):
                        spam_folder = db.query(Folder).filter(
                            Folder.user_id == user_id,
                            Folder.role == "spam"
                        ).first()
                        if spam_folder:
                            target_folder_id = spam_folder.id
                        logger.info(f"IMAP 同步: 黑名单发件人 {sender_addr} → spam 文件夹")
                except Exception as e:
                    logger.warning(f"IMAP 同步: 黑名单检查失败: {e}")

            new_email = Email(
                folder_id=target_folder_id,
                mailbox_address=mailbox_address,
                message_id=msg_id,
                in_reply_to=in_reply_to_raw or None,
                references=references_raw or None,
                thread_id=thread_id,
                subject=decode_mime_header(msg.get("Subject")),
                sender=decode_mime_header(msg.get("From")),
                recipients=decode_mime_header(msg.get("To", "")),
                body_text=body_text,
                body_html=body_html,
                received_at=parse_email_date(msg.get("Date")) or datetime.now(timezone.utc),
                is_read=False,
                is_starred=False,
                is_draft=False,
            )
            db.add(new_email)
            existing_ids.add(msg_id)
            synced += 1
            # 收集新邮件元数据，用于后续触发工作流事件
            _pending_email_events.append({
                "from_email": new_email.sender or "",
                "to_email": mailbox_address,
                "subject": new_email.subject or "",
                "received_at": (new_email.received_at or datetime.now(timezone.utc)).isoformat(),
                "source": "imap_sync"
            })

        if synced > 0:
            db.commit()
            logger.info(f"同步 {mailbox_address}: {synced} 封新邮件")

    except imaplib.IMAP4.error as e:
        err_msg = str(e)
        if "AUTHORIZATIONFAILED" in err_msg or "LOGIN" in err_msg:
            logger.debug(f"IMAP 登录失败 {imap_email}（用户可能不存在于邮件服务器）")
        else:
            logger.error(f"同步 {mailbox_address} IMAP 错误: {e}")
        db.rollback()
    except Exception as e:
        logger.error(f"同步 {mailbox_address} 失败: {e}", exc_info=True)
        db.rollback()
    finally:
        if imap:
            try:
                imap.logout()
            except Exception:
                pass

    return synced


def sync_user_mailbox(db: Session, user: User) -> int:
    """使用 master 用户同步单个用户的邮箱"""
    inbox = db.query(Folder).filter(
        Folder.user_id == user.id,
        Folder.role == "inbox"
    ).first()

    if not inbox:
        logger.warning(f"用户 {user.email} 没有收件箱")
        return 0

    return _sync_imap_inbox(db, user.email, inbox.id, user.email, user_id=user.id)


def sync_temp_mailbox(db: Session, temp_mailbox: TempMailbox) -> int:
    """使用 master 用户同步单个临时邮箱的邮件。

    临时邮箱的邮件存入所有者的收件箱，mailbox_address 记录为临时邮箱地址，
    这样 Pool API 的 get_mailbox_emails 能正确查询到。
    """
    owner = db.query(User).filter(User.id == temp_mailbox.owner_id).first()
    if not owner:
        logger.warning(f"临时邮箱 {temp_mailbox.email} 的所有者不存在")
        return 0

    inbox = db.query(Folder).filter(
        Folder.user_id == owner.id,
        Folder.role == "inbox"
    ).first()

    if not inbox:
        logger.warning(f"所有者 {owner.email} 没有收件箱")
        return 0

    return _sync_imap_inbox(db, temp_mailbox.email, inbox.id, temp_mailbox.email, user_id=owner.id)


def sync_all_mailboxes() -> dict:
    """同步所有用户和临时邮箱的邮件"""
    db = SessionLocal()
    results = {"total": 0, "users": {}, "temp_mailboxes": {}}
    try:
        # 1. 同步注册用户邮箱
        users = db.query(User).all()
        for user in users:
            count = sync_user_mailbox(db, user)
            results["users"][user.email] = count
            results["total"] += count

        # 2. 同步活跃的临时邮箱
        temp_mailboxes = db.query(TempMailbox).filter(
            TempMailbox.is_active == True
        ).all()
        for temp_mb in temp_mailboxes:
            count = sync_temp_mailbox(db, temp_mb)
            results["temp_mailboxes"][temp_mb.email] = count
            results["total"] += count

    finally:
        db.close()
    return results


async def periodic_sync(interval: int = 30):
    """定期同步任务（默认30秒）"""
    while True:
        await asyncio.sleep(interval)
        try:
            results = sync_all_mailboxes()
            if results["total"] > 0:
                logger.info(f"邮件同步完成，共 {results['total']} 封新邮件")

            # 触发收集到的邮件到达事件（限制每批最多 10 个防过载）
            if _pending_email_events:
                events_batch = _pending_email_events[:10]
                _pending_email_events[:10] = []
                try:
                    from core.workflow_service import WorkflowService
                    wf_db = SessionLocal()
                    wf_service = WorkflowService(wf_db)
                    for event_data in events_batch:
                        try:
                            await wf_service.trigger_event("email.received", event_data)
                        except Exception as e:
                            logger.warning(f"email.received 事件触发失败: {e}")
                    wf_db.close()
                except Exception as e:
                    logger.error(f"批量触发 email.received 事件失败: {e}")
        except Exception as e:
            logger.error(f"定期同步失败: {e}")
