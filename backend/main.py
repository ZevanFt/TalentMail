from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from db.database import engine, SessionLocal
from db import models  # 确保导入 models 以注册表
from api import auth, mail, users, folders
from initial import initial_data
from core.mailserver_sync import sync_users_to_mailserver
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

@app.on_event("startup")
def on_startup():
    # Initialize the database and create the initial admin user
    # This function now manages its own DB session
    initial_data.init_db()
    
    # 同步用户到邮件服务器
    # 这个逻辑原本在独立的 sync 服务中，现在集成到 backend 启动流程
    logger.info("开始执行用户同步到邮件服务器...")
    try:
        result = sync_users_to_mailserver()
        logger.info(f"用户同步完成: {result}")
    except Exception as e:
        # 同步失败不应该阻止 backend 启动
        logger.error(f"用户同步失败，但 backend 将继续启动: {e}")

@app.get("/")
def read_root():
    return {"message": "Welcome to TalentMail API"}
