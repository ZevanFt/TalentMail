import smtplib
import os
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid
from schemas import email as email_schema
from core.config import settings
from typing import List, Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_email(
    email_data: email_schema.EmailCreate,
    sender_email: str,
    attachments: Optional[List[dict]] = None,
):
    """
    Connects to the SMTP server and sends an email.
    attachments: List of dicts with keys: filename, content_type, file_path
    """
    # Create the email message (multipart/mixed for attachments)
    msg = MIMEMultipart('mixed')
    
    # Create alternative part for text/html body
    body_part = MIMEMultipart('alternative')
    
    # Format sender and recipients
    sender_name = sender_email.split('@')[0]
    msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), sender_email))
    
    to_addrs = [formataddr((recipient.name, recipient.email)) for recipient in email_data.to]
    cc_addrs = [formataddr((recipient.name, recipient.email)) for recipient in email_data.cc]
    bcc_addrs = [recipient.email for recipient in email_data.bcc]

    msg['To'] = ", ".join(to_addrs)
    if cc_addrs:
        msg['Cc'] = ", ".join(cc_addrs)
        
    msg['Subject'] = Header(email_data.subject, 'utf-8')
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid(domain=sender_email.split('@')[1])

    # Attach body - both plain text and HTML
    body_text = email_data.body_text or email_data.body_html or ""
    body_html = email_data.body_html or f"<pre>{email_data.body_text or ''}</pre>"
    
    body_part.attach(MIMEText(body_text, 'plain', 'utf-8'))
    body_part.attach(MIMEText(body_html, 'html', 'utf-8'))
    msg.attach(body_part)
    
    # Attach files
    if attachments:
        for att in attachments:
            if att.get('file_path') and os.path.exists(att['file_path']):
                with open(att['file_path'], 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=att.get('filename', 'attachment'))
                msg.attach(part)

    all_recipients = [recipient.email for recipient in email_data.to] + \
                     [recipient.email for recipient in email_data.cc] + \
                     bcc_addrs

    try:
        # Connect to the SMTP server
        # Note: For development with docker-mailserver, we don't use SSL/TLS initially.
        # The server is on the internal Docker network.
        server = smtplib.SMTP(settings.MAIL_SERVER, settings.SMTP_PORT)
        
        # If STARTTLS is configured (recommended for production)
        if settings.MAIL_STARTTLS:
            server.starttls()
        
        # Login if credentials are provided
        if settings.USE_CREDENTIALS:
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            
        # Send the email
        # The `from_addr` for the SMTP envelope MUST be the authenticated user.
        # The `From` header in the message (`msg['From']`) can be the actual user.
        # When not using credentials, the from_addr should be the actual sender.
        # When using credentials, it must be the authenticated user.
        from_addr = settings.MAIL_USERNAME if settings.USE_CREDENTIALS else sender_email
        server.sendmail(from_addr, all_recipients, msg.as_string())
        
        log_user = f" via SMTP user {settings.MAIL_USERNAME}" if settings.USE_CREDENTIALS else ""
        logger.info(f"Email sent successfully{log_user}, from {sender_email} to {all_recipients}")
        
        return msg['Message-ID']

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return None
    finally:
        if 'server' in locals() and server:
            server.quit()


def render_template(template_str: str, variables: Dict[str, Any]) -> str:
    """
    渲染模板字符串，替换 {{variable}} 格式的变量
    
    Args:
        template_str: 模板字符串
        variables: 变量字典
    
    Returns:
        渲染后的字符串
    """
    result = template_str
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    return result


def get_email_template(db, template_code: str) -> Optional[dict]:
    """
    从数据库获取邮件模板
    
    Args:
        db: 数据库会话
        template_code: 模板代码
    
    Returns:
        模板字典或 None
    """
    try:
        from db.models.system import SystemEmailTemplate
        template = db.query(SystemEmailTemplate).filter(
            SystemEmailTemplate.code == template_code,
            SystemEmailTemplate.is_active == True
        ).first()
        
        if template:
            return {
                "subject": template.subject,
                "body_html": template.body_html,
                "body_text": template.body_text,
                "variables": template.variables or []
            }
    except Exception as e:
        logger.warning(f"Failed to get email template {template_code}: {e}")
    
    return None


# 默认模板（作为后备）
DEFAULT_TEMPLATES = {
    "verification_code_register": {
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
        "body_text": "您的 TalentMail 注册验证码是：{{code}}，有效期 {{expires_minutes}} 分钟。"
    },
    "verification_code_reset_password": {
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
        "body_text": "您的 TalentMail 密码重置验证码是：{{code}}，有效期 {{expires_minutes}} 分钟。"
    }
}


async def send_verification_code_email(
    to_email: str,
    code: str,
    purpose: str = "register",
    db = None
) -> bool:
    """
    发送验证码邮件
    
    Args:
        to_email: 收件人邮箱
        code: 6位验证码
        purpose: 用途 (register/reset_password)
        db: 数据库会话（可选，用于从数据库获取模板）
    
    Returns:
        bool: 是否发送成功
    """
    # 确定模板代码
    template_code = f"verification_code_{purpose}"
    
    # 准备变量
    variables = {
        "code": code,
        "expires_minutes": "10"
    }
    
    # 尝试从数据库获取模板
    template = None
    if db:
        template = get_email_template(db, template_code)
    
    # 如果数据库没有模板，使用默认模板
    if not template:
        template = DEFAULT_TEMPLATES.get(template_code)
    
    # 如果还是没有模板，使用通用默认模板
    if not template:
        template = {
            "subject": "TalentMail 验证码",
            "body_html": """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #3b82f6;">验证码</h2>
    <p>您的验证码是：</p>
    <div style="background-color: #f3f4f6; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px;">
        <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1f2937;">{{code}}</span>
    </div>
    <p style="color: #6b7280; font-size: 14px;">验证码有效期为 {{expires_minutes}} 分钟。</p>
</div>
""",
            "body_text": "您的验证码是：{{code}}，有效期 {{expires_minutes}} 分钟。"
        }
    
    # 渲染模板
    subject = render_template(template["subject"], variables)
    body_html = render_template(template["body_html"], variables)
    body_text = render_template(template.get("body_text", ""), variables)

    # 创建邮件
    msg = MIMEMultipart('alternative')
    
    # 使用系统邮箱发送
    sender_email = f"noreply@{settings.MAIL_DOMAIN}"
    msg['From'] = formataddr((str(Header("TalentMail", 'utf-8')), sender_email))
    msg['To'] = to_email
    msg['Subject'] = Header(subject, 'utf-8')
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid(domain=settings.MAIL_DOMAIN)
    
    msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
    msg.attach(MIMEText(body_html, 'html', 'utf-8'))

    try:
        server = smtplib.SMTP(settings.MAIL_SERVER, settings.SMTP_PORT)
        
        if settings.MAIL_STARTTLS:
            server.starttls()
        
        if settings.USE_CREDENTIALS:
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        
        from_addr = settings.MAIL_USERNAME if settings.USE_CREDENTIALS else sender_email
        server.sendmail(from_addr, [to_email], msg.as_string())
        
        logger.info(f"Verification code email sent to {to_email} for {purpose}")
        return True

    except Exception as e:
        logger.error(f"Failed to send verification code email to {to_email}: {e}")
        return False
    finally:
        if 'server' in locals() and server:
            server.quit()


async def send_system_email(
    to_email: str,
    template_code: str,
    variables: Dict[str, Any],
    db = None
) -> bool:
    """
    发送系统邮件（通用方法）
    
    Args:
        to_email: 收件人邮箱
        template_code: 模板代码
        variables: 模板变量
        db: 数据库会话
    
    Returns:
        bool: 是否发送成功
    """
    # 尝试从数据库获取模板
    template = None
    if db:
        template = get_email_template(db, template_code)
    
    if not template:
        logger.error(f"Email template not found: {template_code}")
        return False
    
    # 渲染模板
    subject = render_template(template["subject"], variables)
    body_html = render_template(template["body_html"], variables)
    body_text = render_template(template.get("body_text", ""), variables)

    # 创建邮件
    msg = MIMEMultipart('alternative')
    
    # 使用系统邮箱发送
    sender_email = f"noreply@{settings.MAIL_DOMAIN}"
    msg['From'] = formataddr((str(Header("TalentMail", 'utf-8')), sender_email))
    msg['To'] = to_email
    msg['Subject'] = Header(subject, 'utf-8')
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid(domain=settings.MAIL_DOMAIN)
    
    msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
    msg.attach(MIMEText(body_html, 'html', 'utf-8'))

    try:
        server = smtplib.SMTP(settings.MAIL_SERVER, settings.SMTP_PORT)
        
        if settings.MAIL_STARTTLS:
            server.starttls()
        
        if settings.USE_CREDENTIALS:
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        
        from_addr = settings.MAIL_USERNAME if settings.USE_CREDENTIALS else sender_email
        server.sendmail(from_addr, [to_email], msg.as_string())
        
        logger.info(f"System email sent to {to_email} using template {template_code}")
        return True

    except Exception as e:
        logger.error(f"Failed to send system email to {to_email}: {e}")
        return False
    finally:
        if 'server' in locals() and server:
            server.quit()
