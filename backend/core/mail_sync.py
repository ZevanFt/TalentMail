"""邮件同步服务 - 使用 Dovecot Master 用户从 IMAP 同步邮件到数据库"""
import imaplib
import email
import hashlib
import asyncio
import logging
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models.user import User
from db.models.email import Email, Folder
from core.config import settings

logger = logging.getLogger(__name__)

# Dovecot Master 用户配置
MASTER_USER = "sync_master"
MASTER_PASSWORD = "SyncMasterPassword123"


def decode_mime_header(header: str) -> str:
    """解码 MIME 编码的邮件头"""
    if not header:
        return ""
    decoded_parts = []
    for part, charset in decode_header(header):
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(charset or 'utf-8', errors='replace'))
        else:
            decoded_parts.append(part)
    return ''.join(decoded_parts)


def parse_email_date(date_str: str) -> Optional[datetime]:
    """解析邮件日期"""
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str)
    except:
        return None


def get_email_body(msg: email.message.Message) -> tuple:
    """提取邮件正文 (text, html)"""
    body_text, body_html = "", ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if "attachment" in str(part.get("Content-Disposition", "")):
                continue
            payload = part.get_payload(decode=True)
            if payload:
                charset = part.get_content_charset() or 'utf-8'
                content = payload.decode(charset, errors='replace')
                if ctype == "text/plain":
                    body_text = content
                elif ctype == "text/html":
                    body_html = content
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or 'utf-8'
            content = payload.decode(charset, errors='replace')
            if msg.get_content_type() == "text/html":
                body_html = content
            else:
                body_text = content
    return body_text, body_html


def sync_user_mailbox(db: Session, user: User) -> int:
    """使用 master 用户同步单个用户的邮箱"""
    synced = 0
    try:
        # 使用 master 用户登录（格式: user*master_user）
        imap = imaplib.IMAP4(settings.MAIL_SERVER, 143)
        login_user = f"{user.email}*{MASTER_USER}"
        imap.login(login_user, MASTER_PASSWORD)
        
        # 获取用户的收件箱文件夹
        inbox = db.query(Folder).filter(
            Folder.user_id == user.id,
            Folder.role == "inbox"
        ).first()
        
        if not inbox:
            logger.warning(f"用户 {user.email} 没有收件箱")
            imap.logout()
            return 0
        
        # 获取已有的 message_id
        existing_ids = set(
            row[0] for row in db.query(Email.message_id).filter(
                Email.folder_id == inbox.id,
                Email.message_id.isnot(None)
            ).all()
        )
        
        # 选择 INBOX
        status, _ = imap.select('INBOX', readonly=True)
        if status != "OK":
            imap.logout()
            return 0
        
        # 搜索所有邮件
        _, data = imap.search(None, 'ALL')
        email_ids = data[0].split()
        
        for eid in email_ids:
            _, msg_data = imap.fetch(eid, '(RFC822)')
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # 获取 message_id
            msg_id = msg.get("Message-ID", "")
            if msg_id:
                msg_id = msg_id.strip("<>")
            else:
                msg_id = hashlib.sha256(raw_email).hexdigest()[:64]
            
            # 跳过已存在的
            if msg_id in existing_ids:
                continue
            
            body_text, body_html = get_email_body(msg)
            
            new_email = Email(
                folder_id=inbox.id,
                mailbox_address=user.email,
                message_id=msg_id,
                subject=decode_mime_header(msg.get("Subject")),
                sender=decode_mime_header(msg.get("From")),
                recipients=decode_mime_header(msg.get("To", "")),
                body_text=body_text,
                body_html=body_html,
                received_at=parse_email_date(msg.get("Date")) or datetime.utcnow(),
                is_read=False,
                is_starred=False,
                is_draft=False,
            )
            db.add(new_email)
            existing_ids.add(msg_id)
            synced += 1
        
        db.commit()
        imap.logout()
        logger.info(f"同步 {user.email}: {synced} 封新邮件")
        
    except Exception as e:
        logger.error(f"同步用户 {user.email} 失败: {e}")
        db.rollback()
    
    return synced


def sync_all_mailboxes() -> dict:
    """同步所有用户的邮箱"""
    db = SessionLocal()
    results = {"total": 0, "users": {}}
    try:
        users = db.query(User).all()
        for user in users:
            count = sync_user_mailbox(db, user)
            results["users"][user.email] = count
            results["total"] += count
    finally:
        db.close()
    return results


async def periodic_sync(interval: int = 300):
    """定期同步任务（默认5分钟）"""
    while True:
        await asyncio.sleep(interval)
        try:
            logger.info("开始定期邮件同步...")
            results = sync_all_mailboxes()
            logger.info(f"同步完成，共 {results['total']} 封新邮件")
        except Exception as e:
            logger.error(f"定期同步失败: {e}")