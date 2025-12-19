from datetime import timedelta, datetime, timezone
import hashlib
import random
import string
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import and_
from user_agents import parse as parse_user_agent
from pydantic import BaseModel, EmailStr

from core import security
from core.mail import send_verification_code_email
from crud import user as crud_user
from db.database import get_db
from db.models.user import UserSession
from db.models.system import ReservedPrefix, VerificationCode
from schemas.user import UserCreate
from schemas.schemas import Token # Will be moved to schemas.token soon
from api import deps

router = APIRouter()


def get_client_ip(request: Request) -> str:
    """获取客户端真实 IP 地址"""
    # 检查代理头
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


def parse_device_info(user_agent_str: str) -> dict:
    """解析 User-Agent 获取设备信息"""
    try:
        ua = parse_user_agent(user_agent_str)
        browser = f"{ua.browser.family} {ua.browser.version_string}".strip()
        os = f"{ua.os.family} {ua.os.version_string}".strip()
        device_info = f"{browser} on {os}"
        return {
            "browser": browser[:100] if browser else None,
            "os": os[:100] if os else None,
            "device_info": device_info[:255] if device_info else user_agent_str[:255]
        }
    except Exception:
        return {
            "browser": None,
            "os": None,
            "device_info": user_agent_str[:255] if user_agent_str else "Unknown"
        }


def create_session_record(db: Session, user_id: int, token: str, request: Request):
    """创建登录会话记录"""
    user_agent = request.headers.get("User-Agent", "")
    device_info = parse_device_info(user_agent)
    ip_address = get_client_ip(request)
    
    # 使用 token 的哈希值作为标识
    token_hash = hashlib.sha256(token.encode()).hexdigest()[:64]
    
    session = UserSession(
        user_id=user_id,
        token_hash=token_hash,
        device_info=device_info["device_info"],
        browser=device_info["browser"],
        os=device_info["os"],
        ip_address=ip_address,
        is_active=True
    )
    db.add(session)
    db.commit()
    return session


# ============ 验证码相关 Schema ============

class SendVerificationCodeRequest(BaseModel):
    """发送验证码请求"""
    email: EmailStr
    purpose: str = "register"  # register / reset_password


class VerifyCodeRequest(BaseModel):
    """验证验证码请求"""
    email: EmailStr
    code: str
    purpose: str = "register"


class UserCreateWithVerification(BaseModel):
    """带验证码的用户注册请求"""
    email: str  # 要注册的 TalentMail 邮箱
    password: str
    invite_code: str
    verification_email: EmailStr  # 用于验证的外部邮箱
    verification_code: str  # 验证码


# ============ 验证码相关函数 ============

def generate_verification_code() -> str:
    """生成6位数字验证码"""
    return ''.join(random.choices(string.digits, k=6))


def create_verification_code(db: Session, email: str, purpose: str = "register") -> str:
    """创建验证码记录"""
    # 先使之前的验证码失效
    db.query(VerificationCode).filter(
        VerificationCode.email == email,
        VerificationCode.purpose == purpose,
        VerificationCode.is_used == False
    ).update({"is_used": True})
    
    # 生成新验证码
    code = generate_verification_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    verification = VerificationCode(
        email=email,
        code=code,
        purpose=purpose,
        expires_at=expires_at
    )
    db.add(verification)
    db.commit()
    
    return code


def verify_code(db: Session, email: str, code: str, purpose: str = "register") -> bool:
    """验证验证码"""
    verification = db.query(VerificationCode).filter(
        VerificationCode.email == email,
        VerificationCode.purpose == purpose,
        VerificationCode.is_used == False,
        VerificationCode.expires_at > datetime.now(timezone.utc)
    ).order_by(VerificationCode.created_at.desc()).first()
    
    if not verification:
        return False
    
    # 增加尝试次数
    verification.attempts += 1
    
    # 超过5次尝试，使验证码失效
    if verification.attempts > 5:
        verification.is_used = True
        db.commit()
        return False
    
    # 验证码匹配
    if verification.code == code:
        verification.is_used = True
        db.commit()
        return True
    
    db.commit()
    return False


# ============ 验证码 API ============

@router.post("/send-verification-code")
async def send_verification_code(
    request: SendVerificationCodeRequest,
    db: Session = Depends(get_db)
):
    """
    发送验证码到指定邮箱
    """
    # 检查发送频率（1分钟内只能发送一次）
    recent_code = db.query(VerificationCode).filter(
        VerificationCode.email == request.email,
        VerificationCode.purpose == request.purpose,
        VerificationCode.created_at > datetime.now(timezone.utc) - timedelta(minutes=1)
    ).first()
    
    if recent_code:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请1分钟后再试"
        )
    
    # 创建验证码
    code = create_verification_code(db, request.email, request.purpose)
    
    # 发送邮件（传入 db 以便使用数据库中的模板）
    success = await send_verification_code_email(request.email, code, request.purpose, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送验证码失败，请稍后重试"
        )
    
    return {"status": "success", "message": "验证码已发送"}


@router.post("/verify-code")
def verify_verification_code(
    request: VerifyCodeRequest,
    db: Session = Depends(get_db)
):
    """
    验证验证码是否正确（不消耗验证码）
    """
    verification = db.query(VerificationCode).filter(
        VerificationCode.email == request.email,
        VerificationCode.purpose == request.purpose,
        VerificationCode.is_used == False,
        VerificationCode.expires_at > datetime.now(timezone.utc)
    ).order_by(VerificationCode.created_at.desc()).first()
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码无效或已过期"
        )
    
    if verification.attempts >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码尝试次数过多，请重新获取"
        )
    
    if verification.code != request.code:
        verification.attempts += 1
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误"
        )
    
    return {"status": "success", "message": "验证码正确"}


# ============ 注册 API ============

@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Handles user registration with invite code validation.
    (旧版注册接口，不需要邮箱验证)
    """
    # 验证邀请码
    invite = crud_user.validate_invite_code(db, user.invite_code)
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邀请码无效或已过期",
        )
    
    # 提取邮箱前缀（@ 前面的部分）
    email_prefix = user.email.split('@')[0].lower().strip()
    
    # 检查是否是保留前缀
    reserved = db.query(ReservedPrefix).filter(
        ReservedPrefix.prefix == email_prefix,
        ReservedPrefix.is_active == True
    ).first()
    if reserved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"邮箱前缀 '{email_prefix}' 是系统保留前缀，不允许注册",
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
    
    # 使用邀请码（记录使用者）
    crud_user.use_invite_code(db, invite, user_id=new_user.id)
    db.commit()
    
    return {"status": "success", "user_id": new_user.id, "email": new_user.email}


@router.post("/register-with-verification")
def register_user_with_verification(
    user: UserCreateWithVerification,
    db: Session = Depends(get_db)
):
    """
    带邮箱验证的用户注册
    需要先通过 /send-verification-code 发送验证码到外部邮箱
    """
    # 验证邀请码
    invite = crud_user.validate_invite_code(db, user.invite_code)
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邀请码无效或已过期",
        )
    
    # 验证验证码
    if not verify_code(db, user.verification_email, user.verification_code, "register"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码无效或已过期",
        )
    
    # 提取邮箱前缀（@ 前面的部分）
    email_prefix = user.email.split('@')[0].lower().strip()
    
    # 检查是否是保留前缀
    reserved = db.query(ReservedPrefix).filter(
        ReservedPrefix.prefix == email_prefix,
        ReservedPrefix.is_active == True
    ).first()
    if reserved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"邮箱前缀 '{email_prefix}' 是系统保留前缀，不允许注册",
        )
    
    # 检查邮箱是否已注册
    db_user = crud_user.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册",
        )
    
    # 创建用户（使用 UserCreate schema）
    user_create = UserCreate(
        email=user.email,
        password=user.password,
        invite_code=user.invite_code
    )
    new_user = crud_user.create_user(db=db, user=user_create, invite=invite)
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户失败",
        )
    
    # 使用邀请码（记录使用者）
    crud_user.use_invite_code(db, invite, user_id=new_user.id)
    db.commit()
    
    return {"status": "success", "user_id": new_user.id, "email": new_user.email}


@router.post("/login", response_model=Token)
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Logs in a user and returns an access token and a refresh token.
    Also records the login session for security auditing.
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
    
    # 记录登录会话
    try:
        create_session_record(db, user.id, access_token, request)
    except Exception as e:
        # 记录失败不影响登录
        print(f"Failed to create session record: {e}")

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
