from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core import security
from crud import user as crud_user
from db.database import get_db
from schemas.user import UserCreate
from schemas.schemas import Token # Will be moved to schemas.token soon
from datetime import timedelta
from api import deps

router = APIRouter()


@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Handles user registration with invite code validation.
    """
    # 验证邀请码
    invite = crud_user.validate_invite_code(db, user.invite_code)
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邀请码无效或已过期",
        )
    
    # 检查邮箱是否已注册
    db_user = crud_user.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册",
        )
    
    # 创建用户
    new_user = crud_user.create_user(db=db, user=user, invite=invite)
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户失败",
        )
    
    # 使用邀请码
    crud_user.use_invite_code(db, invite)
    db.commit()
    
    return {"status": "success", "user_id": new_user.id, "email": new_user.email}


@router.post("/login", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Logs in a user and returns an access token and a refresh token.
    """
    user = crud_user.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=security.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = security.create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
def refresh_access_token(
    refresh_token: str, db: Session = Depends(get_db)
):
    """
    Refreshes an access token using a refresh token.
    """
    token_data = security.verify_token(refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = crud.get_user_by_email(db, email=token_data.sub)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token, # Return the same refresh token
        "token_type": "bearer",
    }
