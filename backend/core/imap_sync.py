"""
IMAP 邮件同步服务
从 docker-mailserver (Dovecot) 拉取邮件到 PostgreSQL 数据库
"""
import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from db.models.email import Email, Folder
from core.config import settings
import logging

logger = logging.getLogger(__name__)


def decode_mime_header(header: Optional[str]) -> str:
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


def get_email_body(msg: email.message.Message) -> Tuple[str, str]:
    """提取邮件正文 (HTML 和纯文本)"""
    body_html = ""
    body_text = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            
            if "attachment" in content_disposition:
                continue
                
            if content_type == "text/html":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or 'utf-8'
                body_html = payload.decode(charset, errors='replace') if payload else ""
            elif content_type == "text/plain":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or 'utf-8'
                body_text = payload.decode(charset, errors='replace') if payload else ""
    else:
        content_type = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        charset = msg.get_content_charset() or 'utf-8'
        content = payload.decode(charset, errors='replace') if payload else ""
        
        if content_type == "text/html":
            body_html = content
        else:
            body_text = content
    
    return body_html, body_text


def parse_email_message(raw_email: bytes) -> dict:
    """解析原始邮件数据"""
    msg = email.message_from_bytes(raw_email)
    
    message_id = msg.get("Message-ID", "")
    subject = decode_mime_header(msg.get("Subject"))
    sender = decode_mime_header(msg.get("From"))
    to = decode_mime_header(msg.get("To", ""))
    cc = decode_mime_header(msg.get("Cc", ""))
    
    date_str = msg.get("Date")
    received_at = None
    if date_str:
        try:
            received_at = parsedate_to_datetime(date_str)
        except Exception:
            received_at = datetime.utcnow()
    else:
        received_at = datetime.utcnow()
    
    body_html, body_text = get_email_body(msg)
    
    return {
        "message_id": message_id.strip("<>") if message_id else None,
        "subject": subject,
        "sender": sender,
        "recipients": to,
        "cc": cc,
        "body_html": body_html,
        "body_text": body_text,
        "received_at": received_at,
    }


def sync_user_mailbox(
    db: Session,
    user_email: str,
    password: str,
    user_id: int,
    folder_role: str = "inbox"
) -> int:
    """
    同步用户邮箱
    返回新同步的邮件数量
    """
    # 获取用户的目标文件夹
    folder = db.query(Folder).filter(
        Folder.user_id == user_id,
        Folder.role == folder_role
    ).first()
    
    if not folder:
        logger.error(f"用户 {user_id} 没有 {folder_role} 文件夹")
        return 0
    
    # IMAP 文件夹映射
    imap_folder_map = {
        "inbox": "INBOX",
        "sent": "Sent",
        "drafts": "Drafts",
        "trash": "Trash",
        "spam": "Junk",
    }
    imap_folder = imap_folder_map.get(folder_role, "INBOX")
    
    try:
        # 连接 IMAP 服务器 (开发环境用非 SSL)
        if settings.MAIL_USE_SSL:
            imap = imaplib.IMAP4_SSL(settings.MAIL_SERVER, 993)
        else:
            imap = imaplib.IMAP4(settings.MAIL_SERVER, 143)
        
        imap.login(user_email, password)
        logger.info(f"IMAP 登录成功: {user_email}")
        
        # 选择文件夹
        status, _ = imap.select(imap_folder, readonly=True)
        if status != "OK":
            logger.warning(f"无法选择文件夹 {imap_folder}")
            imap.logout()
            return 0
        
        # 搜索所有邮件
        status, messages = imap.search(None, "ALL")
        if status != "OK":
            imap.logout()
            return 0
        
        email_ids = messages[0].split()
        logger.info(f"找到 {len(email_ids)} 封邮件在 {imap_folder}")
        
        # 获取数据库中已有的 message_id
        existing_message_ids = set(
            row[0] for row in db.query(Email.message_id).filter(
                Email.folder_id == folder.id,
                Email.message_id.isnot(None)
            ).all()
        )
        
        new_count = 0
        for email_id in email_ids:
            # 获取邮件
            status, msg_data = imap.fetch(email_id, "(RFC822)")
            if status != "OK":
                continue
            
            raw_email = msg_data[0][1]
            parsed = parse_email_message(raw_email)
            
            # 检查是否已存在
            if parsed["message_id"] and parsed["message_id"] in existing_message_ids:
                continue
            
            # 创建邮件记录
            db_email = Email(
                folder_id=folder.id,
                mailbox_address=user_email,
                message_id=parsed["message_id"],
                subject=parsed["subject"],
                sender=parsed["sender"],
                recipients=parsed["recipients"],
                body_html=parsed["body_html"],
                body_text=parsed["body_text"],
                received_at=parsed["received_at"],
                is_read=False,
                is_starred=False,
                is_draft=False,
            )
            db.add(db_email)
            new_count += 1
            
            if parsed["message_id"]:
                existing_message_ids.add(parsed["message_id"])
        
        db.commit()
        imap.logout()
        
        logger.info(f"同步完成: {new_count} 封新邮件")
        return new_count
        
    except imaplib.IMAP4.error as e:
        logger.error(f"IMAP 错误: {e}")
        return 0
    except Exception as e:
        logger.error(f"同步邮件失败: {e}")
        db.rollback()
        return 0