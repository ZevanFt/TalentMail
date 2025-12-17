from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from db.database import engine, SessionLocal
from db import models  # 确保导入 models 以注册表
from api import auth, mail, users, folders
from initial import initial_data
from core.mailserver_sync import sync_users_to_mailserver
from core.lmtp_server import start_lmtp_server, stop_lmtp_server
from core.mail_sync import periodic_sync
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

# 定时同步任务
sync_task = None

@app.on_event("startup")
async def on_startup():
    global sync_task
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


@app.on_event("shutdown")
async def on_shutdown():
    global sync_task
    logger.info("停止 LMTP 服务...")
    stop_lmtp_server()
    if sync_task:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass


@app.get("/")
def read_root():
    return {"message": "Welcome to TalentMail API"}
