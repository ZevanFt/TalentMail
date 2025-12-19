"""
LMTP 邮件接收服务
接收 Postfix 投递的邮件并存入数据库

架构说明：
- Postfix 通过 dual-deliver.sh 脚本同时投递到 Dovecot 和我们的 LMTP
- 我们的 LMTP 只负责将邮件存入 PostgreSQL 数据库
- Dovecot 负责 IMAP 客户端访问
"""
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import datetime
from typing import Optional, List, Tuple
import asyncio
import os
import uuid
from aiosmtpd.controller import Controller
from aiosmtpd.lmtp import LMTP
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models.email import Email, Folder, TempMailbox, Attachment
from db.models.user import User
from core import websocket as ws_manager
import logging

logger = logging.getLogger(__name__)

UPLOAD_DIR = "/app/uploads/attachments"
os.makedirs(UPLOAD_DIR, exist_ok=True)


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


def get_email_body_and_attachments(msg: email.message.Message) -> Tuple[str, str, List[dict]]:
    """提取邮件正文 (HTML 和纯文本) 和附件"""
    body_html = ""
    body_text = ""
    attachments = []
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            filename = part.get_filename()
            
            # 解码文件名
            if filename:
                filename = decode_mime_header(filename)
            
            # 附件处理
            if "attachment" in content_disposition or (filename and content_type not in ["text/plain", "text/html"]):
                payload = part.get_payload(decode=True)
                if payload and filename:
                    attachments.append({
                        "filename": filename,
                        "content_type": content_type,
                        "data": payload
                    })
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
    
    return body_html, body_text, attachments


def extract_email_address(addr: str) -> str:
    """从 'Name <email@domain>' 格式中提取邮箱地址"""
    if '<' in addr and '>' in addr:
        return addr.split('<')[1].split('>')[0].strip().lower()
    return addr.strip().lower()


class LMTPHandler:
    """LMTP 邮件处理器"""
    
    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        """验证收件人地址"""
        # 提取纯邮箱地址
        email_addr = extract_email_address(address)
        
        db: Session = SessionLocal()
        try:
            # 检查是否是注册用户
            user = db.query(User).filter(User.email == email_addr).first()
            if user:
                envelope.rcpt_tos.append(address)
                return '250 OK'
            
            # 检查是否是临时邮箱
            temp_mailbox = db.query(TempMailbox).filter(
                TempMailbox.email == email_addr,
                TempMailbox.is_active == True
            ).first()
            if temp_mailbox:
                envelope.rcpt_tos.append(address)
                return '250 OK'
            
            logger.warning(f"LMTP: 拒绝投递到未知地址 {email_addr}")
            return '550 User not found'
        finally:
            db.close()
    
    async def handle_DATA(self, server, session, envelope):
        """处理邮件数据"""
        logger.info(f"LMTP: 收到邮件 from={envelope.mail_from} to={envelope.rcpt_tos}")
        
        try:
            # 解析邮件
            msg = email.message_from_bytes(envelope.content)
            
            message_id = msg.get("Message-ID", "")
            if message_id:
                message_id = message_id.strip("<>")
            
            subject = decode_mime_header(msg.get("Subject"))
            sender = decode_mime_header(msg.get("From"))
            to_header = decode_mime_header(msg.get("To", ""))
            cc_header = decode_mime_header(msg.get("Cc", ""))
            
            date_str = msg.get("Date")
            received_at = datetime.utcnow()
            if date_str:
                try:
                    received_at = parsedate_to_datetime(date_str)
                except Exception:
                    pass
            
            body_html, body_text, attachments = get_email_body_and_attachments(msg)
            
            # 为每个收件人创建邮件记录
            db: Session = SessionLocal()
            try:
                for rcpt in envelope.rcpt_tos:
                    rcpt_email = extract_email_address(rcpt)
                    
                    # 先检查是否是临时邮箱
                    temp_mailbox = db.query(TempMailbox).filter(
                        TempMailbox.email == rcpt_email,
                        TempMailbox.is_active == True
                    ).first()
                    
                    if temp_mailbox:
                        # 临时邮箱：存入所有者的收件箱
                        user = db.query(User).filter(User.id == temp_mailbox.owner_id).first()
                        if not user:
                            logger.warning(f"LMTP: 临时邮箱所有者不存在 {rcpt_email}")
                            continue
                    else:
                        # 普通用户邮箱
                        user = db.query(User).filter(User.email == rcpt_email).first()
                        if not user:
                            logger.warning(f"LMTP: 用户不存在 {rcpt_email}")
                            continue
                    
                    inbox = db.query(Folder).filter(
                        Folder.user_id == user.id,
                        Folder.role == "inbox"
                    ).first()
                    
                    if not inbox:
                        logger.error(f"LMTP: 用户 {user.id} 没有收件箱")
                        continue
                    
                    # 检查是否已存在（通过 message_id 去重）
                    if message_id:
                        existing = db.query(Email).filter(
                            Email.folder_id == inbox.id,
                            Email.message_id == message_id
                        ).first()
                        if existing:
                            logger.info(f"LMTP: 邮件已存在，跳过 message_id={message_id}")
                            continue
                    
                    # 创建邮件记录
                    db_email = Email(
                        folder_id=inbox.id,
                        mailbox_address=rcpt_email,
                        message_id=message_id or None,
                        subject=subject,
                        sender=sender,
                        recipients=to_header,
                        body_html=body_html,
                        body_text=body_text,
                        received_at=received_at,
                        is_read=False,
                        is_starred=False,
                        is_draft=False,
                    )
                    db.add(db_email)
                    db.flush()  # 获取 email id
                    
                    # 保存附件
                    for att in attachments:
                        ext = os.path.splitext(att["filename"])[1] if att["filename"] else ""
                        unique_name = f"{uuid.uuid4()}{ext}"
                        file_path = os.path.join(UPLOAD_DIR, unique_name)
                        with open(file_path, "wb") as f:
                            f.write(att["data"])
                        
                        db_attachment = Attachment(
                            email_id=db_email.id,
                            user_id=user.id,
                            filename=att["filename"],
                            content_type=att["content_type"],
                            size=len(att["data"]),
                            file_path=file_path
                        )
                        db.add(db_attachment)
                    
                    logger.info(f"LMTP: 邮件已存入数据库 to={rcpt_email} subject={subject[:50]} attachments={len(attachments)}")
                    
                    # 通知用户有新邮件
                    try:
                        asyncio.create_task(ws_manager.notify_new_email(user.id, {
                            "subject": subject,
                            "sender": sender
                        }))
                    except Exception as e:
                        logger.warning(f"WebSocket 通知失败: {e}")
                
                db.commit()
                
            finally:
                db.close()
            
            return '250 Message accepted for delivery'
            
        except Exception as e:
            logger.error(f"LMTP: 处理邮件失败: {e}", exc_info=True)
            return '451 Temporary failure, please retry'


class LMTPController(Controller):
    """LMTP 控制器，使用 LMTP 协议而非 SMTP"""
    
    def factory(self):
        return LMTP(self.handler)


class LMTPServer:
    """LMTP 服务器"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 24):
        self.host = host
        self.port = port
        self.controller = None
    
    def start(self):
        """启动 LMTP 服务器"""
        handler = LMTPHandler()
        self.controller = LMTPController(
            handler,
            hostname=self.host,
            port=self.port
        )
        self.controller.start()
        logger.info(f"LMTP 服务器已启动: {self.host}:{self.port}")
    
    def stop(self):
        """停止 LMTP 服务器"""
        if self.controller:
            self.controller.stop()
            logger.info("LMTP 服务器已停止")


# 全局 LMTP 服务器实例
lmtp_server: Optional[LMTPServer] = None


def start_lmtp_server(host: str = '0.0.0.0', port: int = 24):
    """启动 LMTP 服务器"""
    global lmtp_server
    lmtp_server = LMTPServer(host, port)
    lmtp_server.start()


def stop_lmtp_server():
    """停止 LMTP 服务器"""
    global lmtp_server
    if lmtp_server:
        lmtp_server.stop()