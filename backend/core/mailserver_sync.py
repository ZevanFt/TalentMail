"""
邮件服务器用户同步模块

此模块负责将数据库中的用户同步到邮件服务器。
原本是一个独立的 sync 服务，现在集成到 backend 中以简化架构。

使用 Python docker SDK 来操作容器，避免需要在容器内安装 docker CLI。
"""

import logging
import os
from typing import Set, List, Optional

import docker
from docker.errors import NotFound, APIError

from db.database import SessionLocal

logger = logging.getLogger(__name__)

# 从环境变量获取配置
MAILSERVER_CONTAINER_NAME = os.getenv("MAILSERVER_CONTAINER_NAME", "talentmail-mailserver-1")
DEFAULT_MAIL_PASSWORD = os.getenv("DEFAULT_MAIL_PASSWORD", "password")

# Docker 客户端（延迟初始化）
_docker_client = None


def get_docker_client():
    """获取 Docker 客户端实例"""
    global _docker_client
    if _docker_client is None:
        try:
            _docker_client = docker.from_env()
        except Exception as e:
            logger.error(f"无法连接到 Docker: {e}")
            return None
    return _docker_client


def get_users_from_db() -> List[str]:
    """从数据库中获取所有用户的邮箱列表"""
    db = SessionLocal()
    try:
        from db.models.user import User
        users = db.query(User.email).all()
        return [user.email for user in users]
    finally:
        db.close()


def get_existing_mail_users() -> Set[str]:
    """获取 mailserver 中已存在的所有邮箱账户"""
    client = get_docker_client()
    if client is None:
        return set()
    
    try:
        container = client.containers.get(MAILSERVER_CONTAINER_NAME)
        result = container.exec_run(["setup", "email", "list"], demux=True)
        
        stdout = result.output[0]
        if stdout is None:
            return set()
        
        output = stdout.decode('utf-8')
        lines = output.strip().split('\n')
        emails = set()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 格式: "* email@domain.com ( 0 / ~ ) [0%]"
            if line.startswith('*'):
                parts = line[2:].strip().split()
                if parts:
                    email = parts[0]
                    if '@' in email:
                        emails.add(email)
            elif '@' in line:
                parts = line.split()
                for part in parts:
                    if '@' in part:
                        emails.add(part)
                        break
        return emails
    except NotFound:
        logger.error(f"容器 {MAILSERVER_CONTAINER_NAME} 未找到")
        return set()
    except APIError as e:
        logger.error(f"Docker API 错误: {e}")
        return set()
    except Exception as e:
        logger.error(f"获取邮箱列表时发生错误: {e}")
        return set()


def create_mail_user(email: str, password: Optional[str] = None) -> bool:
    """
    在 mailserver 中创建一个新的邮箱账户
    
    Args:
        email: 邮箱地址
        password: 明文密码，如果不提供则使用默认密码
    """
    client = get_docker_client()
    if client is None:
        return False
    
    # 使用提供的密码或默认密码
    mail_password = password if password else DEFAULT_MAIL_PASSWORD
    
    try:
        logger.info(f"正在 mailserver 中创建邮箱: {email}")
        container = client.containers.get(MAILSERVER_CONTAINER_NAME)
        result = container.exec_run(["setup", "email", "add", email, mail_password], demux=True)
        
        if result.exit_code == 0:
            logger.info(f"✔ 成功创建邮箱: {email}")
            return True
        else:
            stderr = result.output[1].decode('utf-8') if result.output[1] else ''
            logger.error(f"✖ 创建邮箱 {email} 失败: {stderr}")
            return False
    except NotFound:
        logger.error(f"容器 {MAILSERVER_CONTAINER_NAME} 未找到")
        return False
    except APIError as e:
        logger.error(f"✖ 创建邮箱 {email} 时 Docker API 错误: {e}")
        return False
    except Exception as e:
        logger.error(f"✖ 创建邮箱 {email} 时发生错误: {e}")
        return False


def update_mail_user_password(email: str, password: str) -> bool:
    """
    更新 mailserver 中邮箱账户的密码
    
    Args:
        email: 邮箱地址
        password: 新的明文密码
    """
    client = get_docker_client()
    if client is None:
        return False
    
    try:
        logger.info(f"正在更新邮箱 {email} 的密码...")
        container = client.containers.get(MAILSERVER_CONTAINER_NAME)
        result = container.exec_run(["setup", "email", "update", email, password], demux=True)
        
        if result.exit_code == 0:
            logger.info(f"✔ 成功更新邮箱 {email} 的密码")
            return True
        else:
            stderr = result.output[1].decode('utf-8') if result.output[1] else ''
            logger.error(f"✖ 更新邮箱 {email} 密码失败: {stderr}")
            return False
    except NotFound:
        logger.error(f"容器 {MAILSERVER_CONTAINER_NAME} 未找到")
        return False
    except APIError as e:
        logger.error(f"✖ 更新邮箱 {email} 密码时 Docker API 错误: {e}")
        return False
    except Exception as e:
        logger.error(f"✖ 更新邮箱 {email} 密码时发生错误: {e}")
        return False


def create_or_update_mail_user(email: str, password: str) -> bool:
    """
    创建或更新邮件服务器中的用户
    如果用户不存在则创建，如果存在则更新密码
    
    Args:
        email: 邮箱地址
        password: 明文密码
    """
    existing_users = get_existing_mail_users()
    
    if email in existing_users:
        logger.info(f"邮箱 {email} 已存在，更新密码...")
        return update_mail_user_password(email, password)
    else:
        logger.info(f"邮箱 {email} 不存在，创建新账户...")
        return create_mail_user(email, password)


def sync_users_to_mailserver() -> dict:
    """
    将数据库中的用户同步到邮件服务器
    注意：此函数使用默认密码，仅用于批量同步已存在的用户
    新用户应该在创建时使用 create_mail_user 并传入明文密码
    """
    logger.info("--- 开始同步数据库用户至 Mailserver ---")
    
    result = {"total_db_users": 0, "existing_mail_users": 0, "created": 0, "skipped": 0, "failed": 0}
    
    try:
        db_users = get_users_from_db()
        result["total_db_users"] = len(db_users)
        
        if not db_users:
            logger.info("数据库中没有找到用户，无需同步。")
            return result
        
        logger.info(f"从数据库中找到 {len(db_users)} 个用户。")
        
        mail_users = get_existing_mail_users()
        result["existing_mail_users"] = len(mail_users)
        logger.info(f"Mailserver 中已存在 {len(mail_users)} 个邮箱。")
        
        for user_email in db_users:
            if user_email not in mail_users:
                # 使用默认密码创建（仅用于批量同步）
                if create_mail_user(user_email):
                    result["created"] += 1
                else:
                    result["failed"] += 1
            else:
                logger.debug(f"邮箱 {user_email} 已存在于 mailserver 中，跳过。")
                result["skipped"] += 1
        
        logger.info(f"--- 同步完成: 创建 {result['created']}, 跳过 {result['skipped']}, 失败 {result['failed']} ---")
        
    except Exception as e:
        logger.error(f"同步过程中发生错误: {e}")
    
    return result