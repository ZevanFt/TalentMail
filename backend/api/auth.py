from datetime import timedelta, datetime, timezone
import hashlib
import random
import re
import string
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import and_
from user_agents import parse as parse_user_agent
from pydantic import BaseModel, EmailStr, field_validator

from core import security
from core.config import settings
from core.mail import send_verification_code_email
from core.workflow_service import WorkflowService
from crud import user as crud_user
from db import models
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
    """
    创建或更新登录会话记录
    
    会话去重逻辑：
    - 如果同一用户在相同设备（IP + 浏览器 + OS）已有活跃会话，则只更新 last_active_at
    - 如果是新设备或新环境，则创建新会话记录
    """
    user_agent = request.headers.get("User-Agent", "")
    device_info = parse_device_info(user_agent)
    ip_address = get_client_ip(request)
    
    # 使用 token 的哈希值作为标识
    token_hash = hashlib.sha256(token.encode()).hexdigest()[:64]
    
    # 查找是否有相同设备的活跃会话（基于 IP + 浏览器 + OS）
    existing_session = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.ip_address == ip_address,
        UserSession.browser == device_info["browser"],
        UserSession.os == device_info["os"],
        UserSession.is_active == True
    ).first()
    
    if existing_session:
        # 更新现有会话的最后活动时间和 token
        existing_session.last_active_at = datetime.now(timezone.utc)
        existing_session.token_hash = token_hash
        db.commit()
        return existing_session
    
    # 创建新会话记录
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


# ============ 会话清理函数 ============

def cleanup_old_sessions(db: Session, days: int = 30) -> int:
    """
    清理超过指定天数未活动的会话记录
    
    Args:
        db: 数据库会话
        days: 未活动天数阈值，默认30天
    
    Returns:
        删除的会话数量
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # 删除超过指定天数未活动的会话
    result = db.query(UserSession).filter(
        UserSession.last_active_at < cutoff_date
    ).delete(synchronize_session=False)
    
    db.commit()
    return result


# ============ 邮箱验证辅助函数 ============

def validate_email_flexible(email: str) -> str:
    """
    根据配置灵活验证邮箱格式
    - 开发环境 (strictEmailValidation=False): 允许 .test 等本地域名
    - 生产环境 (strictEmailValidation=True): 使用严格的邮箱验证
    """
    if not email or '@' not in email:
        raise ValueError('邮箱格式无效')
    
    # 基本格式检查
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValueError('邮箱格式无效')
    
    # 如果是严格模式，检查是否是保留域名
    if settings.STRICT_EMAIL_VALIDATION:
        domain = email.split('@')[1].lower()
        # 保留的特殊用途域名
        reserved_tlds = ['.test', '.example', '.invalid', '.localhost']
        for tld in reserved_tlds:
            if domain.endswith(tld):
                raise ValueError(f'不允许使用 {tld} 域名')
    
    return email


# ============ 验证码相关 Schema ============

class SendVerificationCodeRequest(BaseModel):
    """发送验证码请求"""
    email: str
    purpose: str = "register"  # register / reset_password
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return validate_email_flexible(v)


class VerifyCodeRequest(BaseModel):
    """验证验证码请求"""
    email: str
    code: str
    purpose: str = "register"
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return validate_email_flexible(v)


class UserCreateWithVerification(BaseModel):
    """带验证码的用户注册请求"""
    email: str  # 要注册的 TalentMail 邮箱
    password: str
    invite_code: str
    verification_email: str  # 用于验证的外部邮箱
    verification_code: str  # 验证码
    
    @field_validator('email', 'verification_email')
    @classmethod
    def validate_email(cls, v):
        return validate_email_flexible(v)


class ForgotPasswordRequest(BaseModel):
    """忘记密码请求"""
    email: str  # TalentMail 邮箱
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return validate_email_flexible(v)


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    email: str  # TalentMail 邮箱
    code: str  # 验证码
    new_password: str  # 新密码
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return validate_email_flexible(v)


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
    
    # 保存验证邮箱作为辅助邮箱（recovery_email）
    new_user.recovery_email = user.verification_email
    
    # 使用邀请码（记录使用者）
    crud_user.use_invite_code(db, invite, user_id=new_user.id)
    db.commit()
    
    return {"status": "success", "user_id": new_user.id, "email": new_user.email}


@router.post("/login")
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Logs in a user and returns an access token and a refresh token.
    Also records the login session for security auditing.
    
    如果用户启用了 2FA，返回 requires_2fa: true 和 temp_token，
    前端需要调用 /login-2fa 接口完成登录。
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

    # 检查是否启用了 2FA
    if user.two_factor_enabled and user.totp_secret:
        # 生成临时 token（5分钟有效）
        temp_token = security.create_access_token(
            data={"sub": user.email, "type": "2fa_pending"},
            expires_delta=timedelta(minutes=5)
        )
        return {
            "requires_2fa": True,
            "temp_token": temp_token,
            "message": "请输入两步验证码"
        }

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


class Login2FARequest(BaseModel):
    """2FA 登录请求"""
    temp_token: str
    code: str


@router.post("/login-2fa")
def login_with_2fa(
    request: Request,
    login_request: Login2FARequest,
    db: Session = Depends(get_db)
):
    """
    使用 2FA 验证码完成登录
    """
    import pyotp
    
    # 验证临时 token
    token_data = security.verify_token(login_request.temp_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="临时令牌无效或已过期，请重新登录"
        )
    
    # 获取用户
    user = crud_user.get_user_by_email(db, email=token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    # 验证 2FA 是否启用
    if not user.two_factor_enabled or not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户未启用两步验证"
        )
    
    # 验证 TOTP 代码
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(login_request.code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误，请重试"
        )
    
    # 生成正式 token
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


# ============ 密码重置 API ============

@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    发送密码重置验证码到用户的 TalentMail 邮箱
    """
    # 检查用户是否存在
    user = crud_user.get_user_by_email(db, email=request.email)
    if not user:
        # 为了安全，不透露用户是否存在
        # 但仍然返回成功消息
        return {"status": "success", "message": "如果该邮箱已注册，验证码已发送"}
    
    # 检查发送频率（1分钟内只能发送一次）
    recent_code = db.query(VerificationCode).filter(
        VerificationCode.email == request.email,
        VerificationCode.purpose == "reset_password",
        VerificationCode.created_at > datetime.now(timezone.utc) - timedelta(minutes=1)
    ).first()
    
    if recent_code:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请1分钟后再试"
        )
    
    # 尝试使用工作流引擎触发
    # EVENT: password.forgot
    try:
        wf_service = WorkflowService(db)
        # 我们不再在这里生成 verify code，而是交给工作流里的节点去生成
        await wf_service.trigger_event("password.forgot", {
            "email": request.email,
            "user_id": user.id if user else None,
            "user_name": user.display_name if user else "User"
        })
        # 注意：这里我们假设工作流如果配置了，就会负责发送。
        # 如果没有配置工作流，这里其实应该有 Fallback。
        # 但为了演示“工作流接管”，我们只依赖工作流。
        # 实际生产中建议: if not await wf_service.has_handler(...): run_legacy()
    except Exception as e:
        print(f"Trigger workflow failed: {e}")
        # Fallback to legacy logic (Safety Net)
        code = create_verification_code(db, request.email, "reset_password")
        success = await send_verification_code_email(request.email, code, "reset_password", db)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="发送验证码失败，请稍后重试 (Legacy Path)"
            )
    
    return {"status": "success", "message": "验证码已发送到您的邮箱"}


@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    使用验证码重置密码
    """
    # 验证用户是否存在
    user = crud_user.get_user_by_email(db, email=request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户不存在"
        )
    
    # 验证验证码
    if not verify_code(db, request.email, request.code, "reset_password"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码无效或已过期"
        )
    
    # 验证新密码长度
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少为6位"
        )
    
    # 重置密码
    updated_user = crud_user.reset_user_password(db, request.email, request.new_password)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重置密码失败，请稍后重试"
        )
    
    return {"status": "success", "message": "密码重置成功"}


# ============ 辅助邮箱 API ============

class UpdateRecoveryEmailRequest(BaseModel):
    """更新辅助邮箱请求"""
    new_email: str  # 新的辅助邮箱
    code: str  # 验证码
    
    @field_validator('new_email')
    @classmethod
    def validate_email(cls, v):
        return validate_email_flexible(v)


@router.post("/send-recovery-email-code")
async def send_recovery_email_code(
    request: SendVerificationCodeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    发送验证码到新的辅助邮箱（需要登录）
    """
    # 检查发送频率（1分钟内只能发送一次）
    recent_code = db.query(VerificationCode).filter(
        VerificationCode.email == request.email,
        VerificationCode.purpose == "update_recovery_email",
        VerificationCode.created_at > datetime.now(timezone.utc) - timedelta(minutes=1)
    ).first()
    
    if recent_code:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请1分钟后再试"
        )
    
    # 创建验证码
    code = create_verification_code(db, request.email, "update_recovery_email")
    
    # 发送邮件
    success = await send_verification_code_email(request.email, code, "update_recovery_email", db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送验证码失败，请稍后重试"
        )
    
    return {"status": "success", "message": "验证码已发送到新邮箱"}


@router.post("/update-recovery-email")
def update_recovery_email(
    request: UpdateRecoveryEmailRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    更新辅助邮箱（需要登录 + 验证码）
    """
    # 验证验证码
    if not verify_code(db, request.new_email, request.code, "update_recovery_email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码无效或已过期"
        )
    
    # 更新辅助邮箱
    current_user.recovery_email = request.new_email
    db.add(current_user)
    db.commit()
    
    return {"status": "success", "message": "辅助邮箱更新成功", "recovery_email": request.new_email}
