"""外部邮箱同步服务 — 从用户绑定的外部 IMAP 账户拉取邮件到 TalentMail

同步策略：
  - 每 5 分钟扫描所有 sync_enabled=True & is_active=True 的外部账户
  - 使用 IMAP UID 做增量拉取，避免全量扫描
  - 每次最多拉 50 封（防止首次同步阻塞）
  - 连续失败 3 次自动禁用同步并写入 sync_error
  - 每个账户失败不影响其他账户（错误隔离）
"""
import imaplib
import email
import hashlib
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.models.email import Email, Folder
from db.models.external_account import ExternalAccount
from core.config import settings
from core.email_parser import decode_mime_header, parse_email_date, get_email_body
from core.crypto import decrypt_password

logger = logging.getLogger(__name__)

# 每次同步每个账户最多拉取的邮件数
MAX_FETCH_PER_SYNC = 50


def _connect_external_imap(account: ExternalAccount, decrypted_password: str) -> imaplib.IMAP4:
    """连接到外部 IMAP 服务器"""
    if account.imap_ssl:
        imap = imaplib.IMAP4_SSL(account.imap_host, account.imap_port, timeout=30)
    else:
        imap = imaplib.IMAP4(account.imap_host, account.imap_port, timeout=30)
        try:
            imap.starttls()
        except Exception:
            pass  # 部分服务器不支持 STARTTLS
    imap.login(account.username, decrypted_password)
    return imap


def sync_external_account(db: Session, account: ExternalAccount) -> int:
    """同步单个外部账户的邮件到用户收件箱

    Args:
        db: 数据库会话
        account: 外部账户对象

    Returns:
        同步的邮件数量
    """
    synced = 0
    imap = None

    try:
        # 1. 解密密码
        decrypted_pw = decrypt_password(account.password)
        if not decrypted_pw:
            raise ValueError("无法解密外部账户密码")

        # 2. 获取用户收件箱
        inbox = db.query(Folder).filter(
            Folder.user_id == account.user_id,
            Folder.role == "inbox"
        ).first()
        if not inbox:
            logger.warning(f"外部同步: 用户 {account.user_id} 没有收件箱")
            return 0

        # 3. 连接外部 IMAP
        imap = _connect_external_imap(account, decrypted_pw)
        status, _ = imap.select("INBOX", readonly=True)
        if status != "OK":
            raise imaplib.IMAP4.error("SELECT INBOX failed")

        # 4. 增量拉取：使用 UID 搜索
        if account.last_uid:
            # UID 搜索：只拉取大于 last_uid 的邮件
            _, data = imap.uid("search", None, f"UID {account.last_uid + 1}:*")
        else:
            # 首次同步：拉取最新的 MAX_FETCH_PER_SYNC 封
            _, data = imap.search(None, "ALL")

        uid_list = data[0].split() if data[0] else []

        if not uid_list:
            # 没有新邮件
            account.last_sync_at = datetime.now(timezone.utc)
            account.sync_error = None
            account.sync_fail_count = 0
            db.commit()
            return 0

        # 限制拉取数量（取最新的）
        if len(uid_list) > MAX_FETCH_PER_SYNC:
            uid_list = uid_list[-MAX_FETCH_PER_SYNC:]

        # 5. 获取已有的 message_id（按 external_account_id 去重）
        existing_ids = set(
            row[0] for row in db.query(Email.message_id).filter(
                Email.external_account_id == account.id,
                Email.message_id.isnot(None)
            ).all()
        )

        max_uid = account.last_uid or 0

        for uid_bytes in uid_list:
            uid_str = uid_bytes.decode() if isinstance(uid_bytes, bytes) else str(uid_bytes)

            try:
                uid_int = int(uid_str)
            except ValueError:
                continue

            # 使用 UID FETCH
            if account.last_uid:
                _, msg_data = imap.uid("fetch", uid_str, "(RFC822)")
            else:
                # 首次同步用普通 FETCH，uid_str 实际是序列号
                _, msg_data = imap.fetch(uid_str, "(RFC822 UID)")

            if not msg_data or not msg_data[0]:
                continue

            raw_email = msg_data[0][1]
            if not isinstance(raw_email, bytes):
                continue

            msg = email.message_from_bytes(raw_email)

            # 解析 UID（首次同步时从 FETCH 响应提取真实 UID）
            if not account.last_uid and isinstance(msg_data[0][0], bytes):
                # 响应格式: b'1 (RFC822 {...} UID 123)'
                resp_str = msg_data[0][0].decode("ascii", errors="replace")
                import re
                uid_match = re.search(r"UID\s+(\d+)", resp_str)
                if uid_match:
                    uid_int = int(uid_match.group(1))

            # 提取 Message-ID
            msg_id = msg.get("Message-ID", "")
            if msg_id:
                msg_id = msg_id.strip("<>")
            else:
                msg_id = hashlib.sha256(raw_email).hexdigest()[:64]

            # 去重
            if msg_id in existing_ids:
                if uid_int > max_uid:
                    max_uid = uid_int
                continue

            # 解析邮件内容
            body_text, body_html = get_email_body(msg)

            # 线程信息
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

            # 黑名单检查
            target_folder_id = inbox.id
            try:
                from api.spam import is_sender_blocked
                sender_raw = decode_mime_header(msg.get("From", ""))
                sender_addr = sender_raw
                if '<' in sender_addr and '>' in sender_addr:
                    sender_addr = sender_addr.split('<')[1].split('>')[0].strip().lower()
                if sender_addr and is_sender_blocked(db, account.user_id, sender_addr):
                    spam_folder = db.query(Folder).filter(
                        Folder.user_id == account.user_id,
                        Folder.role == "spam"
                    ).first()
                    if spam_folder:
                        target_folder_id = spam_folder.id
                    logger.info(f"外部同步: 黑名单发件人 {sender_addr} → spam")
            except Exception as e:
                logger.warning(f"外部同步: 黑名单检查失败: {e}")

            new_email = Email(
                folder_id=target_folder_id,
                mailbox_address=account.email,  # 外部邮箱地址作为 mailbox_address
                external_account_id=account.id,
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

            if uid_int > max_uid:
                max_uid = uid_int

        # 6. 提交 + 更新账户状态
        if synced > 0:
            db.flush()

        if max_uid > (account.last_uid or 0):
            account.last_uid = max_uid
        account.last_sync_at = datetime.now(timezone.utc)
        account.sync_error = None
        account.sync_fail_count = 0
        db.commit()

        if synced > 0:
            logger.info(f"外部同步 {account.email}: {synced} 封新邮件 (uid={max_uid})")

            # WebSocket 通知用户有新邮件
            try:
                from core import websocket as ws_manager
                asyncio.get_event_loop().create_task(
                    ws_manager.notify_new_email(account.user_id, {
                        "subject": f"{synced} 封来自 {account.email} 的新邮件",
                        "sender": account.email,
                        "source": "external_sync"
                    })
                )
            except Exception as e:
                logger.debug(f"外部同步 WebSocket 通知失败: {e}")

    except imaplib.IMAP4.error as e:
        err_msg = str(e)[:256]
        logger.warning(f"外部同步 {account.email} IMAP 错误: {err_msg}")
        account.sync_error = err_msg
        account.sync_fail_count = (account.sync_fail_count or 0) + 1
        if account.sync_fail_count >= 3:
            account.sync_enabled = False
            logger.warning(f"外部同步 {account.email}: 连续失败 {account.sync_fail_count} 次，已自动禁用")
        db.commit()
    except Exception as e:
        err_msg = str(e)[:256]
        logger.error(f"外部同步 {account.email} 失败: {err_msg}", exc_info=True)
        account.sync_error = err_msg
        account.sync_fail_count = (account.sync_fail_count or 0) + 1
        if account.sync_fail_count >= 3:
            account.sync_enabled = False
            logger.warning(f"外部同步 {account.email}: 连续失败 {account.sync_fail_count} 次，已自动禁用")
        try:
            db.commit()
        except Exception:
            db.rollback()
    finally:
        if imap:
            try:
                imap.logout()
            except Exception:
                pass

    return synced


def sync_all_external_accounts() -> dict:
    """同步所有启用的外部账户"""
    db = SessionLocal()
    results = {"total": 0, "accounts": {}}
    try:
        accounts = db.query(ExternalAccount).filter(
            ExternalAccount.is_active == True,
            ExternalAccount.sync_enabled == True,
        ).all()

        for account in accounts:
            try:
                count = sync_external_account(db, account)
                results["accounts"][account.email] = count
                results["total"] += count
            except Exception as e:
                logger.error(f"外部同步 {account.email} 异常: {e}")
                results["accounts"][account.email] = -1
    finally:
        db.close()
    return results


async def periodic_external_sync(interval: int = 300):
    """定期外部邮箱同步任务（默认 5 分钟）

    使用 asyncio.to_thread 将同步 IMAP 操作放入线程池，
    避免阻塞事件循环。
    """
    # 启动后等待一段时间，让其他服务先初始化
    await asyncio.sleep(30)
    logger.info(f"外部邮箱同步任务启动，间隔 {interval} 秒")

    while True:
        try:
            results = await asyncio.to_thread(sync_all_external_accounts)
            if results["total"] > 0:
                logger.info(f"外部邮箱同步完成，共 {results['total']} 封新邮件")
        except Exception as e:
            logger.error(f"外部邮箱定期同步失败: {e}", exc_info=True)

        await asyncio.sleep(interval)
