from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from db.database import get_db
from api.deps import get_current_user
from db.models.user import User
from db.models.external_account import ExternalAccount

router = APIRouter(prefix="/external-accounts", tags=["external-accounts"])


# 常用邮箱提供商预设配置
PROVIDER_PRESETS = {
    "gmail": {
        "imap_host": "imap.gmail.com",
        "imap_port": 993,
        "imap_ssl": True,
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_ssl": False,
        "smtp_starttls": True,
    },
    "outlook": {
        "imap_host": "outlook.office365.com",
        "imap_port": 993,
        "imap_ssl": True,
        "smtp_host": "smtp.office365.com",
        "smtp_port": 587,
        "smtp_ssl": False,
        "smtp_starttls": True,
    },
    "qq": {
        "imap_host": "imap.qq.com",
        "imap_port": 993,
        "imap_ssl": True,
        "smtp_host": "smtp.qq.com",
        "smtp_port": 587,
        "smtp_ssl": False,
        "smtp_starttls": True,
    },
    "163": {
        "imap_host": "imap.163.com",
        "imap_port": 993,
        "imap_ssl": True,
        "smtp_host": "smtp.163.com",
        "smtp_port": 465,
        "smtp_ssl": True,
        "smtp_starttls": False,
    },
    "126": {
        "imap_host": "imap.126.com",
        "imap_port": 993,
        "imap_ssl": True,
        "smtp_host": "smtp.126.com",
        "smtp_port": 465,
        "smtp_ssl": True,
        "smtp_starttls": False,
    },
    "yeah": {
        "imap_host": "imap.yeah.net",
        "imap_port": 993,
        "imap_ssl": True,
        "smtp_host": "smtp.yeah.net",
        "smtp_port": 465,
        "smtp_ssl": True,
        "smtp_starttls": False,
    },
    "sina": {
        "imap_host": "imap.sina.com",
        "imap_port": 993,
        "imap_ssl": True,
        "smtp_host": "smtp.sina.com",
        "smtp_port": 465,
        "smtp_ssl": True,
        "smtp_starttls": False,
    },
    "aliyun": {
        "imap_host": "imap.aliyun.com",
        "imap_port": 993,
        "imap_ssl": True,
        "smtp_host": "smtp.aliyun.com",
        "smtp_port": 465,
        "smtp_ssl": True,
        "smtp_starttls": False,
    },
    "icloud": {
        "imap_host": "imap.mail.me.com",
        "imap_port": 993,
        "imap_ssl": True,
        "smtp_host": "smtp.mail.me.com",
        "smtp_port": 587,
        "smtp_ssl": False,
        "smtp_starttls": True,
    },
    "yahoo": {
        "imap_host": "imap.mail.yahoo.com",
        "imap_port": 993,
        "imap_ssl": True,
        "smtp_host": "smtp.mail.yahoo.com",
        "smtp_port": 587,
        "smtp_ssl": False,
        "smtp_starttls": True,
    },
    "zoho": {
        "imap_host": "imap.zoho.com",
        "imap_port": 993,
        "imap_ssl": True,
        "smtp_host": "smtp.zoho.com",
        "smtp_port": 587,
        "smtp_ssl": False,
        "smtp_starttls": True,
    },
}


class ExternalAccountCreate(BaseModel):
    email: str
    display_name: Optional[str] = None
    provider: str = "custom"
    username: str
    password: str
    # 自定义服务器配置（provider=custom 时必填）
    imap_host: Optional[str] = None
    imap_port: Optional[int] = 993
    imap_ssl: Optional[bool] = True
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_ssl: Optional[bool] = False
    smtp_starttls: Optional[bool] = True


class ExternalAccountUpdate(BaseModel):
    display_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    sync_enabled: Optional[bool] = None


class ExternalAccountResponse(BaseModel):
    id: int
    email: str
    display_name: Optional[str]
    provider: str
    imap_host: str
    smtp_host: str
    is_active: bool
    sync_enabled: bool
    last_sync_at: Optional[datetime]
    sync_error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/providers")
def get_providers():
    """获取支持的邮箱提供商列表"""
    return {
        "providers": [
            {"id": "gmail", "name": "Gmail", "icon": "gmail"},
            {"id": "outlook", "name": "Outlook / Hotmail", "icon": "outlook"},
            {"id": "icloud", "name": "iCloud", "icon": "icloud"},
            {"id": "yahoo", "name": "Yahoo Mail", "icon": "yahoo"},
            {"id": "qq", "name": "QQ 邮箱", "icon": "qq"},
            {"id": "163", "name": "网易 163 邮箱", "icon": "163"},
            {"id": "126", "name": "网易 126 邮箱", "icon": "126"},
            {"id": "yeah", "name": "Yeah.net 邮箱", "icon": "yeah"},
            {"id": "sina", "name": "新浪邮箱", "icon": "sina"},
            {"id": "aliyun", "name": "阿里云邮箱", "icon": "aliyun"},
            {"id": "zoho", "name": "Zoho Mail", "icon": "zoho"},
            {"id": "custom", "name": "自定义 IMAP/SMTP", "icon": "mail"},
        ]
    }


@router.get("", response_model=List[ExternalAccountResponse])
def list_accounts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """获取用户的外部邮箱账号列表"""
    accounts = db.query(ExternalAccount).filter(ExternalAccount.user_id == user.id).order_by(ExternalAccount.created_at.desc()).all()
    return accounts


@router.post("", response_model=ExternalAccountResponse)
def create_account(data: ExternalAccountCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """添加外部邮箱账号"""
    # 检查是否已存在
    existing = db.query(ExternalAccount).filter(
        ExternalAccount.user_id == user.id,
        ExternalAccount.email == data.email
    ).first()
    if existing:
        raise HTTPException(400, "该邮箱已添加")
    
    # 获取预设配置
    if data.provider in PROVIDER_PRESETS:
        preset = PROVIDER_PRESETS[data.provider]
        imap_host = preset["imap_host"]
        imap_port = preset["imap_port"]
        imap_ssl = preset["imap_ssl"]
        smtp_host = preset["smtp_host"]
        smtp_port = preset["smtp_port"]
        smtp_ssl = preset["smtp_ssl"]
        smtp_starttls = preset["smtp_starttls"]
    else:
        # 自定义配置
        if not data.imap_host or not data.smtp_host:
            raise HTTPException(400, "自定义配置需要提供 IMAP 和 SMTP 服务器地址")
        imap_host = data.imap_host
        imap_port = data.imap_port or 993
        imap_ssl = data.imap_ssl if data.imap_ssl is not None else True
        smtp_host = data.smtp_host
        smtp_port = data.smtp_port or 587
        smtp_ssl = data.smtp_ssl if data.smtp_ssl is not None else False
        smtp_starttls = data.smtp_starttls if data.smtp_starttls is not None else True
    
    account = ExternalAccount(
        user_id=user.id,
        email=data.email,
        display_name=data.display_name,
        provider=data.provider,
        username=data.username,
        password=data.password,  # TODO: 加密存储
        imap_host=imap_host,
        imap_port=imap_port,
        imap_ssl=imap_ssl,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_ssl=smtp_ssl,
        smtp_starttls=smtp_starttls,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.put("/{account_id}", response_model=ExternalAccountResponse)
def update_account(account_id: int, data: ExternalAccountUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """更新外部邮箱账号"""
    account = db.query(ExternalAccount).filter(
        ExternalAccount.id == account_id,
        ExternalAccount.user_id == user.id
    ).first()
    if not account:
        raise HTTPException(404, "账号不存在")
    
    if data.display_name is not None:
        account.display_name = data.display_name
    if data.password is not None:
        account.password = data.password  # TODO: 加密存储
    if data.is_active is not None:
        account.is_active = data.is_active
    if data.sync_enabled is not None:
        account.sync_enabled = data.sync_enabled
    
    db.commit()
    db.refresh(account)
    return account


@router.delete("/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """删除外部邮箱账号"""
    account = db.query(ExternalAccount).filter(
        ExternalAccount.id == account_id,
        ExternalAccount.user_id == user.id
    ).first()
    if not account:
        raise HTTPException(404, "账号不存在")
    
    db.delete(account)
    db.commit()
    return {"message": "删除成功"}


@router.post("/{account_id}/test")
def test_connection(account_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """测试邮箱连接"""
    account = db.query(ExternalAccount).filter(
        ExternalAccount.id == account_id,
        ExternalAccount.user_id == user.id
    ).first()
    if not account:
        raise HTTPException(404, "账号不存在")
    
    # 测试 IMAP 连接
    import imaplib
    try:
        if account.imap_ssl:
            imap = imaplib.IMAP4_SSL(account.imap_host, account.imap_port)
        else:
            imap = imaplib.IMAP4(account.imap_host, account.imap_port)
        imap.login(account.username, account.password)
        imap.logout()
        
        # 清除错误信息
        account.sync_error = None
        db.commit()
        
        return {"status": "success", "message": "连接成功"}
    except Exception as e:
        account.sync_error = str(e)
        db.commit()
        raise HTTPException(400, f"连接失败: {str(e)}")