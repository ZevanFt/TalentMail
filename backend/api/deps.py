from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from core import security
from crud import user as crud_user
from db import models
from db.database import get_db


def get_current_user(
    token: str = Depends(security.oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    """
    Dependency to get the current user from a token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = security.verify_token(token)
    if not token_data:
        raise credentials_exception

    user = crud_user.get_user_by_email(db, email=token_data.sub)
    if user is None:
        raise credentials_exception
        
    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Dependency to get the current active user.
    In the future, you could add a check here for `user.is_active`.
    """
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_user_from_token(db: Session, token: str) -> models.User | None:
    """从 token 获取用户（用于 WebSocket 认证）"""
    token_data = security.verify_token(token)
    if not token_data:
        return None
    return crud_user.get_user_by_email(db, email=token_data.sub)


def get_current_admin_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Dependency to get the current admin user.
    Raises 403 if user is not an admin.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


def get_current_session_id(
    token: str = Depends(security.oauth2_scheme)
) -> Optional[int]:
    """
    从 token 中获取当前会话 ID
    """
    token_data = security.verify_token(token)
    if not token_data:
        return None

    # 从 token_data 中获取 session_id
    return getattr(token_data, 'session_id', None)