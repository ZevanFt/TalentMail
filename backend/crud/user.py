import logging
from sqlalchemy.orm import Session
from db import models
from schemas.user import UserCreate
from core import security
from typing import Optional
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_invite_code(db: Session, code: str) -> Optional[models.InviteCode]:
    """验证邀请码是否有效"""
    invite = db.query(models.InviteCode).filter(models.InviteCode.code == code).first()
    if not invite:
        return None
    if not invite.is_active:
        return None
    if invite.expires_at and invite.expires_at < datetime.now(timezone.utc):
        return None
    if invite.max_uses > 0 and invite.used_count >= invite.max_uses:
        return None
    return invite


def use_invite_code(db: Session, invite: models.InviteCode, user_id: int = None):
    """使用邀请码（增加使用次数并记录使用者）"""
    invite.used_count += 1
    db.add(invite)
    
    # 记录使用者
    if user_id:
        from db.models.billing import InviteCodeUsage
        usage = InviteCodeUsage(
            invite_code_id=invite.id,
            user_id=user_id
        )
        db.add(usage)

def get_user_by_email(db: Session, email: str):
    """
    Retrieves a user from the database by their email address.
    """
    logger.info(f"正在数据库中查询邮箱: {email}")
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        logger.info(f"成功找到用户，ID: {user.id}")
    else:
        logger.info(f"未找到邮箱为 {email} 的用户。")
    return user


def create_default_folders_for_user(db: Session, user_id: int):
    """
    Creates the default set of mail folders for a new user.
    """
    logger.info(f"为用户 ID {user_id} 创建默认文件夹...")
    default_folders = [
        {"name": "Inbox", "role": "inbox"},
        {"name": "Drafts", "role": "drafts"},
        {"name": "Sent", "role": "sent"},
        {"name": "Trash", "role": "trash"},
        {"name": "Spam", "role": "spam"},
        {"name": "Archive", "role": "archive"},
    ]

    try:
        for folder_data in default_folders:
            db_folder = models.Folder(
                user_id=user_id,
                name=folder_data["name"],
                role=folder_data["role"]
            )
            db.add(db_folder)
        
        logger.info(f"成功为用户 ID {user_id} 将 {len(default_folders)} 个默认文件夹添加到会话中。")
    except Exception as e:
        logger.error(f"为用户 ID {user_id} 添加默认文件夹到会话时出错: {e}", exc_info=True)
        raise


def sync_user_to_mailserver(email: str, password: str) -> bool:
    """
    将用户同步到邮件服务器（在用户创建时调用，此时有明文密码）
    
    Args:
        email: 用户邮箱
        password: 明文密码（不会存储，仅用于同步）
    
    Returns:
        bool: 是否同步成功
    """
    try:
        from core.mailserver_sync import create_or_update_mail_user
        result = create_or_update_mail_user(email, password)
        if result:
            logger.info(f"✔ 用户 {email} 已成功同步到邮件服务器")
        else:
            logger.warning(f"⚠ 用户 {email} 同步到邮件服务器失败，但数据库用户已创建")
        return result
    except Exception as e:
        logger.error(f"同步用户 {email} 到邮件服务器时发生错误: {e}", exc_info=True)
        return False


def create_user(db: Session, user: UserCreate, invite: models.InviteCode = None):
    """
    Creates a new user and their default mail folders in the database.
    Also syncs the user to the mailserver with the plaintext password.
    """
    logger.info(f"准备创建用户及其默认文件夹，邮箱: {user.email}")
    try:
        user_data = user.model_dump(exclude={"password", "invite_code"})
        logger.info("用户输入数据已成功序列化。")
        
        hashed_password = security.get_password_hash(user.password)
        logger.info("密码已成功哈希处理。")

        db_user = models.User(**user_data, password_hash=hashed_password)
        logger.info(f"用户 ORM 模型实例已创建: {db_user}")

        db.add(db_user)
        logger.info("用户实例已添加到数据库会话 (session)。")
        
        # Flush here to get the user ID before creating folders
        db.flush()
        logger.info("数据库会话已刷新 (flush)，用户现在拥有一个临时 ID。")

        # Create the default folders for the new user
        create_default_folders_for_user(db=db, user_id=db_user.id)
        
        db.refresh(db_user)
        logger.info(f"用户实例已刷新，从数据库获取到最终 ID: {db_user.id}")
        
        # 同步用户到邮件服务器（使用明文密码，不存储）
        # 注意：即使同步失败，数据库用户也会被创建
        sync_user_to_mailserver(user.email, user.password)
        
        logger.info(f"用户 {user.email} 及默认文件夹创建成功！")
        return db_user
    except Exception as e:
        logger.error(f"创建用户过程中发生严重错误: {e}", exc_info=True)
        db.rollback()
        logger.info("数据库会话已回滚。")
        return None


def authenticate_user(db: Session, email: str, password: str):
    """
    Authenticates a user by checking their email and password.
    """
    logger.info(f"开始认证用户: {email}")
    user = get_user_by_email(db, email=email)
    if not user:
        logger.warning(f"认证失败：用户 '{email}' 不存在。")
        return None
    
    logger.info(f"正在验证用户 '{email}' 的密码...")
    if not security.verify_password(password, user.password_hash):
        logger.warning(f"认证失败：用户 '{email}' 的密码不正确。")
        return None
    
    logger.info(f"用户 '{email}' 认证成功！")
    return user

def get_folder_by_role(db: Session, user_id: int, role: str) -> Optional[models.Folder]:
    """
    Retrieves a system folder for a user by its role (e.g., 'inbox', 'sent').
    """
    logger.info(f"正在为用户 {user_id} 查询角色为 '{role}' 的文件夹...")
    folder = db.query(models.Folder).filter_by(user_id=user_id, role=role).first()
    if folder:
        logger.info(f"成功找到文件夹, ID: {folder.id}, 名称: {folder.name}")
    else:
        logger.warning(f"未找到用户 {user_id} 的 '{role}' 文件夹。")
    return folder


def reset_user_password(db: Session, email: str, new_password: str) -> Optional[models.User]:
    """
    Resets a user's password in both the database and mailserver.
    """
    logger.info(f"正在为用户 '{email}' 重置密码...")
    user = get_user_by_email(db, email=email)
    if not user:
        logger.error(f"重置密码失败：用户 '{email}' 不存在。")
        return None

    try:
        hashed_password = security.get_password_hash(new_password)
        user.password_hash = hashed_password
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"用户 '{email}' 的数据库密码已成功重置。")
        
        # 同步更新邮件服务器密码
        sync_user_to_mailserver(email, new_password)
        
        return user
    except Exception as e:
        logger.error(f"为用户 '{email}' 重置密码时发生错误: {e}", exc_info=True)
        db.rollback()
        return None