import logging
from sqlalchemy.orm import Session
from crud import user as crud_user
from schemas.user import UserCreate
from core.config import settings
from db.database import engine, SessionLocal
from db import models
from db.models.billing import Plan
from db.models.system import ReservedPrefix, SystemEmailTemplate
from initial.init_template_data import init_template_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db() -> None:
    """
    Initializes the database. Creates tables and the initial admin user.
    Manages its own database session to avoid conflicts.
    """
    db = SessionLocal()
    try:
        logger.info("Creating all tables...")
        models.Base.metadata.create_all(bind=engine)
        logger.info("Tables created.")
        _create_initial_admin(db)
        _create_default_plans(db)  # 创建默认套餐
        _create_default_reserved_prefixes(db)  # 创建默认保留前缀
        _create_default_email_templates(db)  # 创建默认邮件模板
        init_template_data(db)  # 初始化模板元数据和全局变量
        _ensure_default_folders_for_all_users(db) # Add this line
        db.commit() # Commit the changes
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
        logger.info("Database session closed after initialization.")


def _create_initial_admin(db: Session) -> None:
    """
    Creates the initial admin user if it doesn't exist.
    Ensures the admin user has the 'admin' role with all permissions.
    """
    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.ADMIN_PASSWORD

    user = crud_user.get_user_by_email(db, email=admin_email)
    if not user:
        user_in = UserCreate(
            email=admin_email,
            password=admin_password,
            display_name="Admin",
            phone=None,
            invite_code="ADMIN_CODE"  # Fix: Use invite_code instead of redemption_code
        )
        user = crud_user.create_user(db, user=user_in)
        if user:
            # Set admin role for the newly created user
            user.role = "admin"
            db.add(user)
            logger.info(f"Initial admin user created with admin role: {admin_email}")
        else:
            logger.error(f"Failed to create initial admin user: {admin_email}")
    else:
        # Ensure existing admin user has admin role
        if user.role != "admin":
            user.role = "admin"
            db.add(user)
            logger.info(f"Updated existing user {admin_email} to admin role.")
        else:
            logger.info(f"Admin user {admin_email} already exists with admin role. Skipping.")


def _create_default_plans(db: Session) -> None:
    """
    创建默认套餐（Free, Pro, Enterprise）
    套餐数据存储在数据库中，管理员可以通过后台修改
    """
    logger.info("检查默认套餐...")
    
    # 检查是否已有套餐
    existing_plans = db.query(Plan).count()
    if existing_plans > 0:
        logger.info(f"已存在 {existing_plans} 个套餐，跳过创建默认套餐")
        return
    
    # 默认套餐配置
    default_plans = [
        {
            "name": "Free",
            "price_monthly": 0,
            "price_yearly": 0,
            "storage_quota_bytes": 1 * 1024 * 1024 * 1024,  # 1GB
            "max_domains": 0,
            "max_aliases": 3,
            "allow_temp_mail": True,
            "max_temp_mailboxes": 3,
            "is_default": True,  # 新用户默认套餐
            "features": {
                "email_tracking": False,
                "priority_support": False,
                "custom_domain": False,
            }
        },
        {
            "name": "Pro",
            "price_monthly": 9.99,
            "price_yearly": 99.99,
            "storage_quota_bytes": 10 * 1024 * 1024 * 1024,  # 10GB
            "max_domains": 3,
            "max_aliases": 20,
            "allow_temp_mail": True,
            "max_temp_mailboxes": 10,
            "is_default": False,
            "features": {
                "email_tracking": True,
                "priority_support": False,
                "custom_domain": True,
            }
        },
        {
            "name": "Enterprise",
            "price_monthly": 29.99,
            "price_yearly": 299.99,
            "storage_quota_bytes": 100 * 1024 * 1024 * 1024,  # 100GB
            "max_domains": 10,
            "max_aliases": 100,
            "allow_temp_mail": True,
            "max_temp_mailboxes": 50,
            "is_default": False,
            "features": {
                "email_tracking": True,
                "priority_support": True,
                "custom_domain": True,
                "api_access": True,
            }
        },
    ]
    
    for plan_data in default_plans:
        plan = Plan(**plan_data)
        db.add(plan)
        logger.info(f"创建套餐: {plan_data['name']}")
    
    logger.info("默认套餐创建完成")


def _create_default_reserved_prefixes(db: Session) -> None:
    """
    创建默认的保留邮箱前缀
    这些前缀不允许普通用户注册，只能由管理员创建
    """
    logger.info("检查默认保留前缀...")
    
    # 检查是否已有保留前缀
    existing_count = db.query(ReservedPrefix).count()
    if existing_count > 0:
        logger.info(f"已存在 {existing_count} 个保留前缀，跳过创建默认前缀")
        return
    
    # 默认保留前缀配置
    default_prefixes = [
        # 系统/管理类（必须保留）
        {"prefix": "admin", "category": "system", "description": "管理员"},
        {"prefix": "administrator", "category": "system", "description": "管理员"},
        {"prefix": "root", "category": "system", "description": "系统管理"},
        {"prefix": "postmaster", "category": "system", "description": "邮件管理员（RFC要求）"},
        {"prefix": "webmaster", "category": "system", "description": "网站管理员"},
        {"prefix": "hostmaster", "category": "system", "description": "域名管理员"},
        {"prefix": "abuse", "category": "system", "description": "滥用举报"},
        {"prefix": "noreply", "category": "system", "description": "系统通知"},
        {"prefix": "no-reply", "category": "system", "description": "系统通知"},
        {"prefix": "system", "category": "system", "description": "系统账号"},
        {"prefix": "mailer-daemon", "category": "system", "description": "邮件系统"},
        
        # 业务/部门类
        {"prefix": "hr", "category": "business", "description": "人力资源"},
        {"prefix": "support", "category": "business", "description": "客服支持"},
        {"prefix": "help", "category": "business", "description": "帮助"},
        {"prefix": "info", "category": "business", "description": "信息咨询"},
        {"prefix": "sales", "category": "business", "description": "销售"},
        {"prefix": "marketing", "category": "business", "description": "市场"},
        {"prefix": "billing", "category": "business", "description": "账单"},
        {"prefix": "contact", "category": "business", "description": "联系"},
        {"prefix": "feedback", "category": "business", "description": "反馈"},
        {"prefix": "service", "category": "business", "description": "服务"},
        
        # 测试/开发类
        {"prefix": "test", "category": "test", "description": "测试"},
        {"prefix": "testing", "category": "test", "description": "测试"},
        {"prefix": "dev", "category": "test", "description": "开发"},
        {"prefix": "demo", "category": "test", "description": "演示"},
        {"prefix": "example", "category": "test", "description": "示例"},
        {"prefix": "sample", "category": "test", "description": "样本"},
        
        # 安全/敏感类
        {"prefix": "security", "category": "security", "description": "安全"},
        {"prefix": "ssl", "category": "security", "description": "SSL证书"},
        {"prefix": "ftp", "category": "security", "description": "FTP"},
        {"prefix": "mail", "category": "security", "description": "邮件"},
        {"prefix": "smtp", "category": "security", "description": "SMTP"},
        {"prefix": "imap", "category": "security", "description": "IMAP"},
        {"prefix": "pop", "category": "security", "description": "POP"},
        {"prefix": "www", "category": "security", "description": "网站"},
        {"prefix": "api", "category": "security", "description": "API"},
        
        # 常见用户名（防止抢注）
        {"prefix": "user", "category": "common", "description": "通用"},
        {"prefix": "guest", "category": "common", "description": "访客"},
        {"prefix": "anonymous", "category": "common", "description": "匿名"},
        {"prefix": "null", "category": "common", "description": "空值"},
        {"prefix": "undefined", "category": "common", "description": "未定义"},
    ]
    
    for prefix_data in default_prefixes:
        prefix = ReservedPrefix(
            prefix=prefix_data["prefix"].lower(),
            category=prefix_data["category"],
            description=prefix_data["description"],
            is_active=True
        )
        db.add(prefix)
    
    logger.info(f"创建了 {len(default_prefixes)} 个默认保留前缀")


def _create_default_email_templates(db: Session) -> None:
    """
    创建默认的系统邮件模板
    包括验证码、欢迎邮件、密码重置等系统邮件
    """
    logger.info("检查默认邮件模板...")
    
    # 检查是否已有模板
    existing_count = db.query(SystemEmailTemplate).count()
    if existing_count > 0:
        logger.info(f"已存在 {existing_count} 个邮件模板，跳过创建默认模板")
        return
    
    # 默认邮件模板
    default_templates = [
        {
            "code": "verification_code_register",
            "name": "注册验证码",
            "category": "system",
            "description": "用户注册时发送的验证码邮件",
            "subject": "TalentMail 注册验证码",
            "body_html": """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #3b82f6;">欢迎注册 TalentMail</h2>
    <p>您好，</p>
    <p>您正在注册 TalentMail 账户，请使用以下验证码完成注册：</p>
    <div style="background-color: #f3f4f6; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px;">
        <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1f2937;">{{code}}</span>
    </div>
    <p style="color: #6b7280; font-size: 14px;">验证码有效期为 {{expires_minutes}} 分钟，请尽快完成验证。</p>
    <p style="color: #6b7280; font-size: 14px;">如果您没有进行此操作，请忽略此邮件。</p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
    <p style="color: #9ca3af; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
</div>
""",
            "body_text": "您的 TalentMail 注册验证码是：{{code}}，有效期 {{expires_minutes}} 分钟。",
            "variables": ["code", "expires_minutes"],
        },
        {
            "code": "verification_code_reset_password",
            "name": "密码重置验证码",
            "category": "system",
            "description": "用户重置密码时发送的验证码邮件",
            "subject": "TalentMail 密码重置验证码",
            "body_html": """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #3b82f6;">密码重置验证</h2>
    <p>您好，</p>
    <p>您正在重置 TalentMail 账户密码，请使用以下验证码：</p>
    <div style="background-color: #f3f4f6; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px;">
        <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1f2937;">{{code}}</span>
    </div>
    <p style="color: #6b7280; font-size: 14px;">验证码有效期为 {{expires_minutes}} 分钟，请尽快完成验证。</p>
    <p style="color: #6b7280; font-size: 14px;">如果您没有进行此操作，请忽略此邮件并确保账户安全。</p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
    <p style="color: #9ca3af; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
</div>
""",
            "body_text": "您的 TalentMail 密码重置验证码是：{{code}}，有效期 {{expires_minutes}} 分钟。",
            "variables": ["code", "expires_minutes"],
        },
        {
            "code": "welcome_email",
            "name": "欢迎邮件",
            "category": "system",
            "description": "用户注册成功后发送的欢迎邮件",
            "subject": "欢迎加入 TalentMail",
            "body_html": """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #3b82f6;">欢迎加入 TalentMail！</h2>
    <p>亲爱的 {{username}}，</p>
    <p>感谢您注册 TalentMail！您的账户已创建成功。</p>
    <p>您的邮箱地址是：<strong>{{email}}</strong></p>
    <div style="background-color: #f3f4f6; padding: 20px; margin: 20px 0; border-radius: 8px;">
        <h3 style="margin-top: 0; color: #1f2937;">开始使用</h3>
        <ul style="color: #4b5563;">
            <li>发送和接收邮件</li>
            <li>管理您的联系人</li>
            <li>使用临时邮箱功能</li>
            <li>自定义您的邮件签名</li>
        </ul>
    </div>
    <p>如有任何问题，请随时联系我们的支持团队。</p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
    <p style="color: #9ca3af; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
</div>
""",
            "body_text": "欢迎加入 TalentMail！您的邮箱地址是：{{email}}。",
            "variables": ["username", "email"],
        },
        {
            "code": "password_changed",
            "name": "密码修改通知",
            "category": "notification",
            "description": "用户密码修改成功后的通知邮件",
            "subject": "TalentMail 密码已修改",
            "body_html": """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #3b82f6;">密码已修改</h2>
    <p>您好 {{username}}，</p>
    <p>您的 TalentMail 账户密码已于 {{changed_at}} 成功修改。</p>
    <p style="color: #ef4444; font-weight: bold;">如果这不是您本人的操作，请立即联系我们的支持团队！</p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
    <p style="color: #9ca3af; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
</div>
""",
            "body_text": "您的 TalentMail 账户密码已于 {{changed_at}} 成功修改。如果这不是您本人的操作，请立即联系我们。",
            "variables": ["username", "changed_at"],
        },
        {
            "code": "login_alert",
            "name": "登录提醒",
            "category": "notification",
            "description": "新设备登录时的提醒邮件",
            "subject": "TalentMail 新设备登录提醒",
            "body_html": """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #3b82f6;">新设备登录提醒</h2>
    <p>您好 {{username}}，</p>
    <p>您的 TalentMail 账户在新设备上登录：</p>
    <div style="background-color: #f3f4f6; padding: 15px; margin: 20px 0; border-radius: 8px;">
        <p style="margin: 5px 0;"><strong>时间：</strong>{{login_time}}</p>
        <p style="margin: 5px 0;"><strong>设备：</strong>{{device_info}}</p>
        <p style="margin: 5px 0;"><strong>IP 地址：</strong>{{ip_address}}</p>
    </div>
    <p style="color: #ef4444;">如果这不是您本人的操作，请立即修改密码！</p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
    <p style="color: #9ca3af; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
</div>
""",
            "body_text": "您的 TalentMail 账户在新设备上登录。时间：{{login_time}}，设备：{{device_info}}，IP：{{ip_address}}。如果这不是您本人的操作，请立即修改密码！",
            "variables": ["username", "login_time", "device_info", "ip_address"],
        },
        {
            "code": "subscription_expiring",
            "name": "订阅即将到期",
            "category": "notification",
            "description": "用户订阅即将到期的提醒邮件",
            "subject": "TalentMail 订阅即将到期",
            "body_html": """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #f59e0b;">订阅即将到期</h2>
    <p>您好 {{username}}，</p>
    <p>您的 TalentMail <strong>{{plan_name}}</strong> 套餐将于 <strong>{{expires_at}}</strong> 到期。</p>
    <p>为了继续享受完整功能，请及时续费。</p>
    <div style="text-align: center; margin: 20px 0;">
        <a href="{{renew_url}}" style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">立即续费</a>
    </div>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
    <p style="color: #9ca3af; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
</div>
""",
            "body_text": "您的 TalentMail {{plan_name}} 套餐将于 {{expires_at}} 到期，请及时续费。",
            "variables": ["username", "plan_name", "expires_at", "renew_url"],
        },
    ]
    
    for template_data in default_templates:
        template = SystemEmailTemplate(
            code=template_data["code"],
            name=template_data["name"],
            category=template_data["category"],
            description=template_data["description"],
            subject=template_data["subject"],
            body_html=template_data["body_html"].strip(),
            body_text=template_data["body_text"],
            variables=template_data["variables"],
            is_active=True
        )
        db.add(template)
    
    logger.info(f"创建了 {len(default_templates)} 个默认邮件模板")


def _ensure_default_folders_for_all_users(db: Session) -> None:
    """
    Checks all users and creates default folders for those who don't have them.
    This is useful for applying the folder structure to existing users.
    """
    logger.info("Checking for users missing default folders...")
    users = db.query(models.User).all()
    for user in users:
        # A simple way to check is to see if they have an 'inbox' folder.
        inbox_folder = crud_user.get_folder_by_role(db, user_id=user.id, role="inbox")
        if not inbox_folder:
            logger.info(f"User {user.email} (ID: {user.id}) is missing default folders. Creating them now...")
            try:
                crud_user.create_default_folders_for_user(db, user_id=user.id)
                logger.info(f"Successfully added folder creation tasks for user {user.email}.")
            except Exception as e:
                logger.error(f"Failed to create folders for user {user.email}: {e}", exc_info=True)
                # We will let the main exception handler catch this and rollback.
                raise
        else:
            logger.info(f"User {user.email} already has an inbox. Assuming all folders are present.")
    logger.info("Folder check for all users complete.")
