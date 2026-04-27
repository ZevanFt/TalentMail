from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import asyncio
from db.database import engine, SessionLocal
from db import models  # 确保导入 models 以注册表
from api import auth, mail, users, folders, tracking, invite, pool, signatures, attachments, billing, reserved_prefixes, email_templates, totp, blocklist, aliases, tags, contacts, external_accounts, drive, automation, automation_temp_mailboxes, workflows, workflow_templates, changelog, spam, health, api_keys, proxy, system_mail, templates, email_import, calendar, encryption
from api.deps import get_current_user_from_token
from api.auth import cleanup_old_sessions
from initial import initial_data
from core.mailserver_sync import sync_users_to_mailserver
from core.lmtp_server import start_lmtp_server, stop_lmtp_server
from core.mail_sync import periodic_sync
from core.external_sync import periodic_external_sync
from core.temp_mailbox_lifecycle import run_temp_mailbox_maintenance
from core.scheduled_sender import check_scheduled_emails
from core.config import settings
from core import websocket as ws_manager
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 后台任务注册表 + 心跳追踪
_background_tasks: dict[str, asyncio.Task] = {}
_task_heartbeats: dict[str, float] = {}  # 任务名→最后心跳时间戳
_task_factories: dict[str, tuple] = {}   # 任务名→(工厂函数, kwargs)


def _register_task(name: str, coro_factory, **kwargs):
    """注册并启动一个后台任务，支持自动恢复"""
    _task_factories[name] = (coro_factory, kwargs)
    task = asyncio.create_task(coro_factory(**kwargs))
    task.add_done_callback(lambda t, n=name: _on_task_done(n, t))
    _background_tasks[name] = task
    _task_heartbeats[name] = datetime.now(timezone.utc).timestamp()
    return task


def _on_task_done(name: str, task: asyncio.Task):
    """后台任务完成/崩溃的回调 — 自动重启"""
    exc = task.exception() if not task.cancelled() else None
    if exc:
        logger.error(f"[TaskMonitor] 后台任务 '{name}' 崩溃: {exc}，5 秒后自动重启")
        # 延迟重启，避免快速崩溃循环
        asyncio.get_running_loop().call_later(5, _restart_task, name)
    else:
        logger.warning(f"[TaskMonitor] 后台任务 '{name}' 意外退出")


def _restart_task(name: str):
    """重启一个已崩溃的后台任务"""
    if name not in _task_factories:
        return
    factory, kwargs = _task_factories[name]
    logger.info(f"[TaskMonitor] 重启后台任务 '{name}'")
    task = asyncio.create_task(factory(**kwargs))
    task.add_done_callback(lambda t, n=name: _on_task_done(n, t))
    _background_tasks[name] = task
    _task_heartbeats[name] = datetime.now(timezone.utc).timestamp()


def update_task_heartbeat(name: str):
    """由后台任务调用，更新心跳时间"""
    _task_heartbeats[name] = datetime.now(timezone.utc).timestamp()


def get_task_status() -> dict:
    """获取所有后台任务的健康状态"""
    now = datetime.now(timezone.utc).timestamp()
    status = {}
    for name, task in _background_tasks.items():
        last_hb = _task_heartbeats.get(name, 0)
        age = now - last_hb
        status[name] = {
            "running": not task.done(),
            "last_heartbeat_ago_sec": round(age, 1),
        }
    return status


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
                deleted_count = 0
                # 分批处理，每批最多 100 个，避免大量孤儿附件一次性加载到内存
                while True:
                    batch = db.query(Attachment).filter(
                        Attachment.email_id.is_(None),
                        Attachment.created_at < cutoff
                    ).limit(100).all()
                    if not batch:
                        break
                    for att in batch:
                        if att.file_path and os.path.exists(att.file_path):
                            try:
                                os.remove(att.file_path)
                            except OSError:
                                pass
                        db.delete(att)
                        deleted_count += 1
                    db.commit()
                if deleted_count > 0:
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
                    # 一次 JOIN 查询获取所有受影响用户（替代 N+1 循环）
                    expired_ids = [e.id for e in expired]
                    user_ids = set(
                        uid for (uid,) in db.query(Folder.user_id).join(
                            Email, Email.folder_id == Folder.id
                        ).filter(Email.id.in_(expired_ids)).distinct().all()
                    )
                    for email in expired:
                        email.snoozed_until = None
                    db.commit()
                    logger.info(f"[Snooze] 唤醒了 {len(expired)} 封贪睡邮件")
                    for uid in user_ids:
                        await ws_manager.broadcast_to_user(uid, "snooze_wakeup")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[Snooze] 贪睡检查失败: {e}")


async def periodic_audit_log_cleanup(interval: int = 86400):
    """
    定期清理过期审计日志（默认每 24 小时执行一次）。
    保留天数由 settings.AUDIT_LOG_RETENTION_DAYS 控制（默认 30 天）。
    使用分批删除避免长事务锁表。
    """
    from db.models.system import ApiKeyAuditLog
    from datetime import timedelta

    BATCH_SIZE = 5000

    while True:
        await asyncio.sleep(interval)
        try:
            db = SessionLocal()
            try:
                cutoff = datetime.now(timezone.utc) - timedelta(days=settings.AUDIT_LOG_RETENTION_DAYS)
                total_deleted = 0

                while True:
                    # 分批删除，每批 BATCH_SIZE 条，避免长事务
                    subq = (
                        db.query(ApiKeyAuditLog.id)
                        .filter(ApiKeyAuditLog.created_at < cutoff)
                        .limit(BATCH_SIZE)
                        .subquery()
                    )
                    deleted = (
                        db.query(ApiKeyAuditLog)
                        .filter(ApiKeyAuditLog.id.in_(subq))
                        .delete(synchronize_session=False)
                    )
                    db.commit()
                    total_deleted += deleted
                    if deleted < BATCH_SIZE:
                        break  # 最后一批，不满则结束

                if total_deleted > 0:
                    logger.info(
                        "审计日志清理完成: 删除 %d 条 (保留 %d 天, cutoff=%s)",
                        total_deleted, settings.AUDIT_LOG_RETENTION_DAYS, cutoff.isoformat(),
                    )
            finally:
                db.close()
        except Exception as e:
            logger.error(f"审计日志清理失败: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
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

    # ── 注册所有后台任务（崩溃自动重启 + 心跳追踪）──
    logger.info("注册后台任务...")
    _register_task("mail_sync", periodic_sync, interval=30)
    _register_task("external_sync", periodic_external_sync, interval=300)
    _register_task("session_cleanup", periodic_session_cleanup, interval=86400)
    _register_task("temp_mailbox_cleanup", periodic_temp_mailbox_cleanup, interval=600)
    _register_task("scheduled_sender", check_scheduled_emails, interval=60)
    _register_task("orphan_attachment_cleanup", periodic_orphan_attachment_cleanup, interval=3600)
    _register_task("snooze_check", periodic_snooze_check, interval=60)
    _register_task("audit_log_cleanup", periodic_audit_log_cleanup, interval=86400)
    logger.info("已注册 %d 个后台任务（崩溃自动恢复已启用）", len(_background_tasks))

    # 启动时先执行一次会话清理
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

    # ── Shutdown：统一取消所有已注册后台任务 ──
    logger.info("停止 LMTP 服务...")
    stop_lmtp_server()

    logger.info("取消 %d 个后台任务...", len(_background_tasks))
    for name, task in _background_tasks.items():
        task.cancel()
    for name, task in _background_tasks.items():
        try:
            await task
        except asyncio.CancelledError:
            pass
    _background_tasks.clear()
    _task_factories.clear()
    _task_heartbeats.clear()

    # 关闭数据库连接池
    engine.dispose()
    logger.info("TalentMail 已安全停止")


app = FastAPI(
    title="TalentMail API",
    description="Backend API for TalentMail.",
    version="2.0.0",
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
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
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
app.include_router(system_mail.router, prefix="/api", tags=["System Email"])
app.include_router(templates.router, prefix="/api", tags=["User Templates"])
app.include_router(email_import.router, prefix="/api", tags=["Email Import"])
app.include_router(calendar.router, prefix="/api", tags=["Calendar"])
app.include_router(encryption.router, prefix="/api", tags=["Encryption"])


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
