import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from schemas.user import UserRead, UserPasswordReset
from db import models
from api import deps
from fastapi import HTTPException
from crud import user as crud_user

# 配置日志记录器
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=UserRead)
def read_users_me(current_user: models.User = Depends(deps.get_current_active_user)):
    """
    获取当前用户信息。
    """
    logger.info(f"用户 {current_user.email} 正在请求个人信息。")
    return current_user


@router.post("/reset-password-dev", status_code=200)
def reset_password_dev(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserPasswordReset,
):
    """
    Development-only endpoint to reset a user's password without authentication.
    """
    logger.info(f"开发接口：正在请求重置用户 '{user_in.email}' 的密码。")
    
    user = crud_user.reset_user_password(
        db=db, email=user_in.email, new_password=user_in.new_password
    )
    
    if not user:
        logger.error(f"开发接口：重置密码失败，用户 '{user_in.email}' 未找到或发生数据库错误。")
        raise HTTPException(
            status_code=404,
            detail=f"User with email {user_in.email} not found or DB error.",
        )
        
    logger.info(f"开发接口：用户 '{user_in.email}' 的密码已成功重置。")
    return {"msg": f"Password for user {user_in.email} has been reset successfully."}