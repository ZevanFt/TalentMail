from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import asyncio
from db.database import engine, SessionLocal
from db import models  # 确保导入 models 以注册表
from api import auth, mail, users, folders, tracking, invite, pool, signatures, attachments, billing, reserved_prefixes, email_templates, totp, blocklist, aliases, tags, contacts, external_accounts, drive, automation, automation_temp_mailboxes, workflows, workflow_templates, changelog, spam, health, api_keys, proxy
from api.deps import get_current_user_from_token
from api.auth import cleanup_old_sessions
from initial import initial_data
from core.mailserver_sync import sync_users_to_mailserver
from core.lmtp_server import start_lmtp_server, stop_lmtp_server
from core.mail_sync import periodic_sync
from core.temp_mailbox_lifecycle import run_temp_mailbox_maintenance
from core.scheduled_sender import check_scheduled_emails
from core.config import settings
from core import websocket as ws_manager
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 定时任务
sync_task = None
cleanup_task = None
temp_mailbox_cleanup_task = None
scheduled_sender_task = None
orphan_attachment_task = None
snooze_task = None


async def periodic_session_cleanup(interval: int = 86400):
    """
    定期清理旧会话的任务
    默认每24小时执行一次,清理30天未活动的会话
    """
    while True:
        await asyncio.sleep(interval)  # 等待指定间隔
        try:
            db = SessionLocal()
            try:
                deleted_count = cleanup_old_sessions(db, days=30)
                if deleted_count > 0:
                    logger.info(f"已清理 {deleted_count} 个过期会话记录")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"清理会话记录失败: {e}")


async def periodic_temp_mailbox_cleanup(interval: int = 600):
    """
    定时推进临时邮箱生命周期并按策略执行清理
    interval 为轮询检查间隔（秒），实际清理频率由数据库策略控制。
    """
    while True:
        await asyncio.sleep(interval)
        try:
            db = SessionLocal()
            try:
                result = run_temp_mailbox_maintenance(db, force_cleanup=False)
                if result["expired_count"] > 0 or result["cleanup_ran"]:
                    logger.info(
                        f"临时邮箱维护完成: expired={result['expired_count']}, "
                        f"purged={result['purged_count']}, ran={result['cleanup_ran']}"
                    )
            finally:
                db.close()
        except Exception as e:
            logger.error(f"临时邮箱维护任务失败: {e}")


async def periodic_orphan_attachment_cleanup(interval: int = 3600):
    """
    定期清理孤儿附件（已上传但未关联到任何邮件、超过 24 小时的附件）
    防止用户上传附件后不发送邮件导致磁盘泄漏。
    """
    import os
    from db.models.email import Attachment
    from datetime import timedelta
    while True:
        await asyncio.sleep(interval)
        try:
            db = SessionLocal()
            try:
                cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
                orphans = db.query(Attachment).filter(
                    Attachment.email_id.is_(None),
                    Attachment.created_at < cutoff
                ).all()
                deleted_count = 0
                for att in orphans:
                    if att.file_path and os.path.exists(att.file_path):
                        try:
                            os.remove(att.file_path)
                        except OSError:
                            pass
                    db.delete(att)
                    deleted_count += 1
                if deleted_count > 0:
                    db.commit()
                    logger.info(f"已清理 {deleted_count} 个孤儿附件")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"孤儿附件清理失败: {e}")


async def periodic_snooze_check(interval: int = 60):
    """定期检查贪睡到期的邮件，清除 snoozed_until 使其重新出现在收件箱"""
    from db.models.email import Email, Folder
    while True:
        await asyncio.sleep(interval)
        try:
            db = SessionLocal()
            try:
                now = datetime.now(timezone.utc)
                # 查找所有 snoozed_until 已过期的邮件
                expired = db.query(Email).filter(
                    Email.snoozed_until != None,  # noqa: E711
                    Email.snoozed_until <= now,
                ).all()
                if expired:
                    for email in expired:
                        email.snoozed_until = None
                    db.commit()
                    logger.info(f"[Snooze] 唤醒了 {len(expired)} 封贪睡邮件")
                    # 按用户分组发 WebSocket 通知
                    user_ids = set()
                    for email in expired:
                        folder = db.query(Folder).filter(Folder.id == email.folder_id).first()
                        if folder:
                            user_ids.add(folder.user_id)
                    for uid in user_ids:
                        await ws_manager.broadcast_to_user(uid, "snooze_wakeup")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[Snooze] 贪睡检查失败: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global sync_task, cleanup_task, temp_mailbox_cleanup_task, scheduled_sender_task, orphan_attachment_task, snooze_task
    # Initialize the database and create the initial admin user
    initial_data.init_db()

    # 同步用户到邮件服务器
    logger.info("开始执行用户同步到邮件服务器...")
    try:
        result = sync_users_to_mailserver()
        logger.info(f"用户同步完成: {result}")
    except Exception as e:
        logger.error(f"用户同步失败，但 backend 将继续启动: {e}")

    # 启动 LMTP 服务器接收邮件
    if settings.ENABLE_INTERNAL_LMTP:
        logger.info("启动 LMTP 邮件接收服务...")
        try:
            start_lmtp_server(host='0.0.0.0', port=24)
            logger.info("LMTP 服务启动成功，监听端口 24")
        except Exception as e:
            logger.error(f"LMTP 服务启动失败: {e}")
    else:
        logger.info("已禁用内置 LMTP 服务，使用 mailserver 的 Dovecot/IMAP 同步链路")

    # 启动定时邮件同步任务（每30秒，确保临时邮箱验证码及时到达）
    logger.info("启动定时邮件同步任务（间隔30秒）...")
    sync_task = asyncio.create_task(periodic_sync(interval=30))

    # 启动定时会话清理任务（每24小时）
    logger.info("启动定时会话清理任务（间隔24小时）...")
    cleanup_task = asyncio.create_task(periodic_session_cleanup(interval=86400))

    # 启动临时邮箱生命周期维护任务（每10分钟检查一次）
    logger.info("启动临时邮箱生命周期维护任务（检查间隔10分钟）...")
    temp_mailbox_cleanup_task = asyncio.create_task(periodic_temp_mailbox_cleanup(interval=600))

    # 启动定时邮件发送调度器（每60秒检查到期的定时邮件）
    logger.info("启动定时邮件发送调度器（间隔60秒）...")
    scheduled_sender_task = asyncio.create_task(check_scheduled_emails(interval=60))

    # 启动孤儿附件清理任务（每小时检查一次，清理 24 小时前未关联的上传）
    logger.info("启动孤儿附件清理任务（间隔1小时）...")
    orphan_attachment_task = asyncio.create_task(periodic_orphan_attachment_cleanup(interval=3600))

    # 启动贪睡邮件唤醒任务（每60秒检查到期的贪睡邮件）
    logger.info("启动贪睡邮件唤醒任务（间隔60秒）...")
    snooze_task = asyncio.create_task(periodic_snooze_check(interval=60))

    # 启动时先执行一次清理
    try:
        db = SessionLocal()
        try:
            deleted_count = cleanup_old_sessions(db, days=30)
            if deleted_count > 0:
                logger.info(f"启动时清理了 {deleted_count} 个过期会话记录")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"启动时清理会话记录失败: {e}")

    yield

    # Shutdown
    logger.info("停止 LMTP 服务...")
    stop_lmtp_server()
    if sync_task:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
    if temp_mailbox_cleanup_task:
        temp_mailbox_cleanup_task.cancel()
        try:
            await temp_mailbox_cleanup_task
        except asyncio.CancelledError:
            pass
    if scheduled_sender_task:
        scheduled_sender_task.cancel()
        try:
            await scheduled_sender_task
        except asyncio.CancelledError:
            pass
    if orphan_attachment_task:
        orphan_attachment_task.cancel()
        try:
            await orphan_attachment_task
        except asyncio.CancelledError:
            pass
    if snooze_task:
        snooze_task.cancel()
        try:
            await snooze_task
        except asyncio.CancelledError:
            pass

    # 关闭数据库连接池
    engine.dispose()
    logger.info("TalentMail 已安全停止")


app = FastAPI(
    title="TalentMail API",
    description="Backend API for TalentMail.",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS - 根据环境设置允许的域名
def _get_cors_origins():
    """根据当前环境返回允许的 CORS 源"""
    if settings.CURRENT_ENVIRONMENT == "production":
        base_domain = settings.BASE_DOMAIN
        web_prefix = settings.WEB_PREFIX
        return [
            f"https://{web_prefix}.{base_domain}",
            f"https://{base_domain}",
        ]
    # 开发环境允许所有
    return ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(mail.router, prefix="/api/emails", tags=["Emails"])
app.include_router(folders.router, prefix="/api/folders", tags=["Folders"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(tracking.router, prefix="/api/track", tags=["Tracking"])
app.include_router(invite.router, prefix="/api/invite", tags=["Invite"])
app.include_router(pool.router, prefix="/api/pool", tags=["Pool"])
app.include_router(signatures.router, prefix="/api/signatures", tags=["Signatures"])
app.include_router(attachments.router, prefix="/api/attachments", tags=["Attachments"])
app.include_router(billing.router, prefix="/api/billing", tags=["Billing"])
app.include_router(reserved_prefixes.router, prefix="/api/prefixes", tags=["Reserved Prefixes"])
app.include_router(email_templates.router, prefix="/api/email-templates", tags=["Email Templates"])
app.include_router(totp.router, prefix="/api/2fa", tags=["Two-Factor Authentication"])
app.include_router(blocklist.router, prefix="/api/blocklist", tags=["Blocklist"])
app.include_router(aliases.router, prefix="/api/aliases", tags=["Aliases"])
app.include_router(tags.router, prefix="/api", tags=["Tags"])
app.include_router(contacts.router, prefix="/api", tags=["Contacts"])
app.include_router(external_accounts.router, prefix="/api", tags=["External Accounts"])
app.include_router(drive.router, prefix="/api", tags=["Drive"])
app.include_router(automation.router, prefix="/api", tags=["Automation"])
app.include_router(automation_temp_mailboxes.router, prefix="/api", tags=["Automation Temp Mailboxes"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(workflow_templates.router, prefix="/api/workflow-templates", tags=["Workflow Templates"])
app.include_router(changelog.router, prefix="/api/changelogs", tags=["Changelog"])
app.include_router(spam.router, prefix="/api/spam", tags=["Spam Management"])
app.include_router(api_keys.router, prefix="/api/api-keys", tags=["API Keys"])
app.include_router(proxy.router, prefix="/api", tags=["Proxy"])


@app.get("/")
def read_root():
    return {"message": "Welcome to TalentMail API"}


@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket 端点，用于实时推送新邮件通知"""
    try:
        # 验证 token 获取用户
        db = SessionLocal()
        try:
            user = get_current_user_from_token(db, token)
            if not user:
                await websocket.close(code=4001)
                return
            user_id = user.id
        finally:
            db.close()

        await ws_manager.connect(websocket, user_id)
        try:
            while True:
                # 等待客户端消息，90 秒超时自动检测僵死连接
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=90)
                    if data == "ping":
                        await websocket.send_text("pong")
                except asyncio.TimeoutError:
                    # 服务端主动 ping，检测连接是否存活
                    try:
                        await websocket.send_text("ping")
                    except Exception:
                        break  # 发送失败，连接已死
        except WebSocketDisconnect:
            pass
        finally:
            ws_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
