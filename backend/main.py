from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from db.database import engine, SessionLocal
from db import models  # 确保导入 models 以注册表
from api import auth, mail, users, folders, tracking, invite, pool, signatures, attachments, billing, reserved_prefixes, email_templates, totp, blocklist, aliases, tags, contacts, external_accounts, drive, automation, workflows, workflow_templates, changelog
from api.deps import get_current_user_from_token
from api.auth import cleanup_old_sessions
from initial import initial_data
from core.mailserver_sync import sync_users_to_mailserver
from core.lmtp_server import start_lmtp_server, stop_lmtp_server
from core.mail_sync import periodic_sync
from core import websocket as ws_manager
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TalentMail API",
    description="Backend API for TalentMail.",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(workflow_templates.router, prefix="/api/workflow-templates", tags=["Workflow Templates"])
app.include_router(changelog.router, prefix="/api/changelogs", tags=["Changelog"])

# 定时任务
sync_task = None
cleanup_task = None


async def periodic_session_cleanup(interval: int = 86400):
    """
    定期清理旧会话的任务
    默认每24小时执行一次，清理30天未活动的会话
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

@app.on_event("startup")
async def on_startup():
    global sync_task, cleanup_task
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
    logger.info("启动 LMTP 邮件接收服务...")
    try:
        start_lmtp_server(host='0.0.0.0', port=24)
        logger.info("LMTP 服务启动成功，监听端口 24")
    except Exception as e:
        logger.error(f"LMTP 服务启动失败: {e}")
    
    # 启动定时邮件同步任务（每5分钟）
    logger.info("启动定时邮件同步任务（间隔5分钟）...")
    sync_task = asyncio.create_task(periodic_sync(interval=300))
    
    # 启动定时会话清理任务（每24小时）
    logger.info("启动定时会话清理任务（间隔24小时）...")
    cleanup_task = asyncio.create_task(periodic_session_cleanup(interval=86400))
    
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


@app.on_event("shutdown")
async def on_shutdown():
    global sync_task, cleanup_task
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
                # 保持连接，等待客户端消息（心跳）
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
