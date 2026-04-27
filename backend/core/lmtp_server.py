"""
LMTP 邮件接收服务
接收 Postfix 投递的邮件并存入数据库

架构说明：
- Postfix 通过 dual-deliver.sh 脚本同时投递到 Dovecot 和我们的 LMTP
- 我们的 LMTP 只负责将邮件存入 PostgreSQL 数据库
- Dovecot 负责 IMAP 客户端访问
"""
import email
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
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


async def _fire_email_received_event(wf_service, wf_db, event_data: dict):
    """触发邮件到达事件，独立 DB session，失败不影响主流程"""
    try:
        await wf_service.trigger_event("email.received", event_data)
    except Exception as e:
        logger.error(f"email.received 工作流执行失败: {e}", exc_info=True)
    finally:
        try:
            wf_db.close()
        except Exception:
            pass


from core.email_parser import decode_mime_header, get_email_body_and_attachments, extract_email_address


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

            # 检查是否是活跃的别名
            from db.models.email import Alias
            alias = db.query(Alias).filter(
                Alias.alias_email == email_addr,
                Alias.is_active == True
            ).first()
            if alias:
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
            received_at = datetime.now(timezone.utc)
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
                            # 检查是否是别名
                            from db.models.email import Alias
                            alias = db.query(Alias).filter(
                                Alias.alias_email == rcpt_email,
                                Alias.is_active == True
                            ).first()
                            if alias:
                                user = db.query(User).filter(User.id == alias.user_id).first()
                                if not user:
                                    logger.warning(f"LMTP: 别名所有者不存在 {rcpt_email}")
                                    continue
                                logger.info(f"LMTP: 别名邮件 {rcpt_email} → 用户 {user.email}")
                            else:
                                logger.warning(f"LMTP: 用户不存在 {rcpt_email}")
                                continue
                    
                    inbox = db.query(Folder).filter(
                        Folder.user_id == user.id,
                        Folder.role == "inbox"
                    ).first()

                    if not inbox:
                        logger.error(f"LMTP: 用户 {user.id} 没有收件箱")
                        continue

                    # 黑名单检查：拦截的邮件投入 spam 文件夹
                    target_folder = inbox
                    sender_addr = extract_email_address(sender) if sender else ""
                    if sender_addr:
                        try:
                            from api.spam import is_sender_blocked
                            if is_sender_blocked(db, user.id, sender_addr):
                                spam_folder = db.query(Folder).filter(
                                    Folder.user_id == user.id,
                                    Folder.role == "spam"
                                ).first()
                                if spam_folder:
                                    target_folder = spam_folder
                                logger.info(f"LMTP: 黑名单发件人 {sender_addr} → spam 文件夹")
                        except Exception as e:
                            logger.warning(f"LMTP: 黑名单检查失败: {e}")

                    # 检查是否已存在（通过 message_id 去重，检查 inbox 和 spam 两个文件夹）
                    if message_id:
                        existing = db.query(Email).filter(
                            Email.message_id == message_id,
                            Email.folder_id.in_(
                                db.query(Folder.id).filter(Folder.user_id == user.id)
                            )
                        ).first()
                        if existing:
                            logger.info(f"LMTP: 邮件已存在，跳过 message_id={message_id}")
                            continue

                    # 提取线程信息
                    in_reply_to_header = msg.get("In-Reply-To", "")
                    if in_reply_to_header:
                        in_reply_to_header = in_reply_to_header.strip().strip("<>")
                    references_header = msg.get("References", "")
                    thread_id = None
                    if in_reply_to_header:
                        parent = db.query(Email.thread_id, Email.message_id).filter(
                            Email.message_id == in_reply_to_header
                        ).first()
                        if parent and parent.thread_id:
                            thread_id = parent.thread_id
                        else:
                            thread_id = in_reply_to_header

                    # 使用 savepoint 隔离每个收件人的写入，失败不影响其他收件人
                    try:
                        savepoint = db.begin_nested()
                        # 创建邮件记录
                        # PGP 加密检测
                        _is_pgp = bool(body_text and '-----BEGIN PGP MESSAGE-----' in body_text) or \
                                  bool(body_html and '-----BEGIN PGP MESSAGE-----' in body_html)

                        db_email = Email(
                            folder_id=target_folder.id,
                            mailbox_address=rcpt_email,
                            message_id=message_id or None,
                            in_reply_to=in_reply_to_header or None,
                            references=references_header or None,
                            thread_id=thread_id,
                            subject=subject,
                            sender=sender,
                            recipients=to_header,
                            body_html=body_html,
                            body_text=body_text,
                            received_at=received_at,
                            is_read=False,
                            is_starred=False,
                            is_draft=False,
                            is_encrypted=_is_pgp,
                            encryption_type='pgp' if _is_pgp else None,
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

                        savepoint.commit()
                        logger.info(f"LMTP: 邮件已存入数据库 to={rcpt_email} subject={subject[:50]} attachments={len(attachments)}")
                    except Exception as e:
                        savepoint.rollback()
                        logger.error(f"LMTP: 保存邮件失败 to={rcpt_email}: {e}")
                        continue

                    # 通知用户有新邮件
                    try:
                        asyncio.create_task(ws_manager.notify_new_email(user.id, {
                            "subject": subject,
                            "sender": sender
                        }))
                    except Exception as e:
                        logger.warning(f"WebSocket 通知失败: {e}")

                    # 触发邮件到达工作流事件（fire-and-forget，不阻塞投递）
                    try:
                        from core.workflow_service import WorkflowService
                        wf_db = SessionLocal()
                        wf_service = WorkflowService(wf_db)
                        asyncio.create_task(_fire_email_received_event(wf_service, wf_db, {
                            "email_id": str(db_email.id),
                            "from_email": sender,
                            "to_email": rcpt_email,
                            "subject": subject or "",
                            "user_id": str(user.id),
                            "has_attachments": str(len(attachments) > 0).lower(),
                            "received_at": (db_email.received_at or datetime.now(timezone.utc)).isoformat()
                        }))
                    except Exception as e:
                        logger.warning(f"触发 email.received 事件失败: {e}")

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