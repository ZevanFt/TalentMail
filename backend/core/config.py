import json
import os
from pathlib import Path
from pydantic import EmailStr
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # --- Sensitive settings loaded from .env file ---
    ADMIN_PASSWORD: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL_DOCKER: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    JWT_ALGORITHM: str

    # --- Non-sensitive settings loaded from config.json ---
    APP_NAME: str = "TalentMail"
    CURRENT_ENVIRONMENT: str = "development"
    BASE_DOMAIN: str = "localhost"
    WEB_PREFIX: str = "mail"
    MAIL_SERVER_PREFIX: Optional[str] = None
    MAIL_SERVER: Optional[str] = None
    SMTP_PORT: int = 1025
    STRICT_EMAIL_VALIDATION: bool = False
    MAIL_STARTTLS: bool = False
    MAIL_USE_SSL: bool = False  # 开发环境用非 SSL IMAP (143)，生产环境用 SSL (993)
    USE_CREDENTIALS: bool = False # Default to false, should be enabled in production
    MAIL_USERNAME: Optional[str] = None # Will be dynamically generated
    MAIL_PASSWORD: Optional[str] = None # Will be sourced from ADMIN_PASSWORD

    # --- Dynamically generated attributes ---
    DOMAIN: str = ""
    API_BASE_URL: str = ""
    ADMIN_EMAIL: str = "" # Changed back to str to break circular import

    class Config:
        env_file = ".env"
        extra = 'ignore'

def load_config() -> Settings:
    settings = Settings()
    config_path = Path("/app/config.json")
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    
    with open(config_path, "r") as f:
        config_json = json.load(f)

    # 优先使用环境变量中的 CURRENT_ENVIRONMENT，否则使用 config.json 中的配置
    env_name = os.getenv("CURRENT_ENVIRONMENT", config_json.get("currentEnvironment", "development"))
    env_settings = config_json.get("environments", {}).get(env_name, {})

    settings.APP_NAME = config_json.get("appName", settings.APP_NAME)
    settings.CURRENT_ENVIRONMENT = env_name
    
    for key, value in env_settings.items():
        # 强制用 config.json 的值覆盖
        snake_case_key = ''.join(['_'+c.lower() if c.isupper() else c for c in key]).lstrip('_').upper()
        if hasattr(settings, snake_case_key):
            setattr(settings, snake_case_key, value)

    # 允许环境变量 DOMAIN 覆盖 BASE_DOMAIN (这对 Docker 部署至关重要)
    env_domain = os.getenv("DOMAIN")
    if env_domain:
        settings.BASE_DOMAIN = env_domain

    settings.DOMAIN = f"{settings.WEB_PREFIX}.{settings.BASE_DOMAIN}"
    settings.API_BASE_URL = f"https://{settings.DOMAIN}/api"
    
    if settings.MAIL_SERVER is None:
        if settings.MAIL_SERVER_PREFIX:
            settings.MAIL_SERVER = f"{settings.MAIL_SERVER_PREFIX}.{settings.BASE_DOMAIN}"
        else:
            raise ValueError("Mail server is not configured in config.json for the current environment")

    settings.ADMIN_EMAIL = f"admin@{settings.BASE_DOMAIN}"
    
    # --- Configure mail credentials dynamically ---
    # The username is always the admin of the current domain.
    settings.MAIL_USERNAME = settings.ADMIN_EMAIL
    # The password for the mail server's admin account is the same as the app's admin account.
    settings.MAIL_PASSWORD = settings.ADMIN_PASSWORD

    return settings

settings = load_config()
