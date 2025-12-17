import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# --- 基础路径和环境加载 ---
# 加载项目根目录下的 .env 文件
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

# --- 环境设置 ---
# 可选值: 'development' 或 'production'
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# --- 域名和服务器配置 ---
DOMAIN = "talenting.vip"
DEV_DOMAIN = "talenting.test"
MAIL_SERVER_HOSTNAME = f"maillink.{DOMAIN}"
SERVER_IP = os.getenv('SERVER_IP', "127.0.0.1")

# --- 根据环境进行动态配置 ---
if ENVIRONMENT == 'development':
    # --- 开发环境配置 ---
    WEB_DOMAIN = os.getenv('NUXT_PUBLIC_WEB_DOMAIN', f"mail.{DEV_DOMAIN}")
    DEBUG = True
    
    # 从 .env 文件读取本地数据库配置
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('DB_NAME')

    # 对密码中的特殊字符进行 URL 编码
    encoded_password = quote_plus(db_password)

    # 构建数据库连接字符串
    DATABASE_URL = f"postgresql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"

    # 开发时邮件指向 Mailpit
    SMTP_HOST = os.getenv('SMTP_HOST', "127.0.0.1")
    SMTP_PORT = int(os.getenv('SMTP_PORT', 1025))
    SMTP_USER = ""
    SMTP_PASS = ""
else:
    # --- 生产环境配置 ---
    WEB_DOMAIN = f"mail.{DOMAIN}"
    DEBUG = False
    # 生产环境应从环境变量中读取完整的 DATABASE_URL
    DATABASE_URL = os.getenv('DATABASE_URL_PROD')
    
    # 生产时邮件指向真实的邮件服务器
    SMTP_HOST = "127.0.0.1"
    SMTP_PORT = 25
    SMTP_USER = ""
    SMTP_PASS = ""

# --- 通用配置 ---
# 应用密钥 (建议生产环境中从环境变量读取)
