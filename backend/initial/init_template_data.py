"""
初始化模板元数据和全局变量
"""
import logging
from sqlalchemy.orm import Session
from db.models.template import TemplateMetadata, GlobalVariable
from db.models.system import SystemEmailTemplate

logger = logging.getLogger(__name__)

TEMPLATE_METADATA = [
    {
        "code": "verification_code_register",
        "name": "注册验证码",
        "category": "auth",
        "description": "用户注册时发送的验证码邮件",
        "trigger_description": "用户在注册页面输入邮箱并点击'获取验证码'时触发",
        "variables": [
            {"key": "code", "label": "验证码", "type": "string", "example": "123456", "required": True},
            {"key": "expires_minutes", "label": "过期时间(分钟)", "type": "number", "example": "10", "required": True}
        ],
        "default_subject": "TalentMail 注册验证码",
        "default_body_html": """
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
        "default_body_text": "您的 TalentMail 注册验证码是：{{code}}，有效期 {{expires_minutes}} 分钟。",
        "is_system": True,
        "sort_order": 1
    },
    {
        "code": "verification_code_reset_password",
        "name": "重置密码验证码",
        "category": "auth",
        "description": "用户忘记密码时发送的验证码邮件",
        "trigger_description": "用户在忘记密码页面输入邮箱并点击'获取验证码'时触发",
        "variables": [
            {"key": "code", "label": "验证码", "type": "string", "example": "888888", "required": True},
            {"key": "expires_minutes", "label": "过期时间(分钟)", "type": "number", "example": "10", "required": True}
        ],
        "default_subject": "TalentMail 密码重置验证码",
        "default_body_html": """
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
        "default_body_text": "您的 TalentMail 密码重置验证码是：{{code}}，有效期 {{expires_minutes}} 分钟。",
        "is_system": True,
        "sort_order": 2
    },
    {
        "code": "welcome_email",
        "name": "欢迎新用户",
        "category": "notification",
        "description": "用户注册成功后发送的欢迎邮件",
        "trigger_description": "用户完成注册后自动发送",
        "variables": [
            {"key": "user_name", "label": "用户名", "type": "string", "example": "张三", "required": False},
            {"key": "user_email", "label": "用户邮箱", "type": "string", "example": "user@example.com", "required": True},
            {"key": "login_url", "label": "登录链接", "type": "url", "example": "https://mail.example.com/login", "required": True}
        ],
        "default_subject": "欢迎加入 TalentMail",
        "default_body_html": """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #3b82f6;">欢迎加入 TalentMail</h2>
    <p>亲爱的 {{user_name|default:"用户"}}，</p>
    <p>感谢您注册 TalentMail！我们很高兴能为您提供安全、高效的邮件服务。</p>
    <p>您的账户 {{user_email}} 已成功创建。</p>
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{login_url}}" style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">立即登录</a>
    </div>
    <p>如果您有任何问题，请随时联系我们的支持团队。</p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
    <p style="color: #9ca3af; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
</div>
""",
        "default_body_text": "欢迎加入 TalentMail！您的账户 {{user_email}} 已成功创建。请访问 {{login_url}} 登录。",
        "is_system": True,
        "sort_order": 10
    },
    {
        "code": "login_alert",
        "name": "异地登录提醒",
        "category": "auth",
        "description": "检测到新设备或异地登录时发送的安全提醒",
        "trigger_description": "用户从新设备或新IP登录时触发",
        "variables": [
            {"key": "user_name", "label": "用户名", "type": "string", "example": "张三", "required": False},
            {"key": "login_time", "label": "登录时间", "type": "datetime", "example": "2024-12-29 10:30:00", "required": True},
            {"key": "login_ip", "label": "登录IP", "type": "string", "example": "192.168.1.1", "required": True},
            {"key": "login_device", "label": "登录设备", "type": "string", "example": "Chrome on Windows", "required": True},
            {"key": "login_location", "label": "登录地点", "type": "string", "example": "北京市", "required": False}
        ],
        "default_subject": "TalentMail 异地登录提醒",
        "default_body_html": """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #ef4444;">异地登录提醒</h2>
    <p>亲爱的 {{user_name|default:"用户"}}，</p>
    <p>我们要检测到您的账户有新的登录活动：</p>
    <ul style="background-color: #fef2f2; padding: 20px 40px; border-radius: 8px; color: #991b1b;">
        <li><strong>时间：</strong> {{login_time}}</li>
        <li><strong>IP地址：</strong> {{login_ip}}</li>
        <li><strong>地点：</strong> {{login_location|default:"未知"}}</li>
        <li><strong>设备：</strong> {{login_device}}</li>
    </ul>
    <p>如果这是您本人的操作，请忽略此邮件。</p>
    <p><strong>如果这不是您本人的操作，请立即修改密码！</strong></p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
    <p style="color: #9ca3af; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
</div>
""",
        "default_body_text": "异地登录提醒：您的账户于 {{login_time}} 在 {{login_location}} (IP: {{login_ip}}) 登录。如果不是您本人操作，请立即修改密码。",
        "is_system": True,
        "sort_order": 3
    },
    {
        "code": "storage_warning",
        "name": "存储空间警告",
        "category": "notification",
        "description": "用户存储空间即将用尽时发送的警告",
        "trigger_description": "用户存储空间使用超过80%时触发",
        "variables": [
            {"key": "user_name", "label": "用户名", "type": "string", "example": "张三", "required": False},
            {"key": "used_percent", "label": "已用百分比", "type": "number", "example": "85", "required": True},
            {"key": "used_space", "label": "已用空间", "type": "string", "example": "850MB", "required": True},
            {"key": "total_space", "label": "总空间", "type": "string", "example": "1GB", "required": True},
            {"key": "upgrade_url", "label": "升级链接", "type": "url", "example": "https://...", "required": False}
        ],
        "default_subject": "TalentMail 存储空间不足警告",
        "default_body_html": """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #f59e0b;">存储空间不足警告</h2>
    <p>亲爱的 {{user_name|default:"用户"}}，</p>
    <p>您的邮箱存储空间已使用 <strong>{{used_percent}}%</strong>。</p>
    <div style="background-color: #f3f4f6; height: 20px; border-radius: 10px; margin: 20px 0; overflow: hidden;">
        <div style="background-color: #f59e0b; width: {{used_percent}}%; height: 100%;"></div>
    </div>
    <p>已用：{{used_space}} / 总计：{{total_space}}</p>
    <p>为了不影响邮件收发，请及时清理不需要的邮件或升级您的存储空间。</p>
    {{#if upgrade_url}}
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{upgrade_url}}" style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">升级空间</a>
    </div>
    {{/if}}
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
    <p style="color: #9ca3af; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
</div>
""",
        "default_body_text": "存储空间不足警告：您的邮箱存储空间已使用 {{used_percent}}% ({{used_space}}/{{total_space}})。请及时清理或升级。",
        "is_system": True,
        "sort_order": 11
    },
    {
        "code": "file_share_notification",
        "name": "文件分享通知",
        "category": "collaboration",
        "description": "用户分享文件给他人时发送的通知",
        "trigger_description": "用户在网盘中分享文件并填写接收者邮箱时触发",
        "variables": [
            {"key": "sender_name", "label": "分享者名称", "type": "string", "example": "张三", "required": True},
            {"key": "sender_email", "label": "分享者邮箱", "type": "string", "example": "zhangsan@example.com", "required": True},
            {"key": "file_name", "label": "文件名", "type": "string", "example": "季度报表.pdf", "required": True},
            {"key": "file_size", "label": "文件大小", "type": "string", "example": "2.5MB", "required": False},
            {"key": "share_url", "label": "分享链接", "type": "url", "example": "https://...", "required": True},
            {"key": "share_password", "label": "访问密码", "type": "string", "example": "1234", "required": False},
            {"key": "expires_at", "label": "过期时间", "type": "datetime", "example": "2024-12-31", "required": False}
        ],
        "default_subject": "{{sender_name}} 向您分享了文件",
        "default_body_html": """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #3b82f6;">文件分享通知</h2>
    <p>您好，</p>
    <p><strong>{{sender_name}}</strong> ({{sender_email}}) 向您分享了一个文件：</p>
    <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <p style="margin: 0; font-weight: bold; font-size: 18px;">{{file_name}}</p>
        <p style="margin: 5px 0 0 0; color: #6b7280;">大小：{{file_size|default:"未知"}}</p>
        {{#if expires_at}}
        <p style="margin: 5px 0 0 0; color: #6b7280;">有效期至：{{expires_at}}</p>
        {{/if}}
    </div>
    {{#if share_password}}
    <p>访问密码：<strong>{{share_password}}</strong></p>
    {{/if}}
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{share_url}}" style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">查看文件</a>
    </div>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
    <p style="color: #9ca3af; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
</div>
""",
        "default_body_text": "{{sender_name}} 向您分享了文件 {{file_name}}。请访问 {{share_url}} 查看。",
        "is_system": True,
        "sort_order": 20
    },
    {
        "code": "invite_registration",
        "name": "邀请注册",
        "category": "collaboration",
        "description": "邀请他人注册 TalentMail 时发送的邀请函",
        "trigger_description": "管理员或用户生成邀请链接并发送时触发",
        "variables": [
            {"key": "inviter_name", "label": "邀请人名称", "type": "string", "example": "张三", "required": True},
            {"key": "inviter_email", "label": "邀请人邮箱", "type": "string", "example": "zhangsan@example.com", "required": True},
            {"key": "invite_url", "label": "邀请链接", "type": "url", "example": "https://...", "required": True},
            {"key": "invite_code", "label": "邀请码", "type": "string", "example": "ABC123", "required": True},
            {"key": "expires_at", "label": "过期时间", "type": "datetime", "example": "2024-12-31", "required": False}
        ],
        "default_subject": "{{inviter_name}} 邀请您加入 TalentMail",
        "default_body_html": """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #3b82f6;">邀请函</h2>
    <p>您好，</p>
    <p><strong>{{inviter_name}}</strong> ({{inviter_email}}) 邀请您注册 TalentMail。</p>
    <p>TalentMail 是一个安全、高效的企业级邮件系统。</p>
    <div style="background-color: #f3f4f6; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px;">
        <p style="margin-bottom: 10px;">您的邀请码：</p>
        <span style="font-size: 24px; font-weight: bold; letter-spacing: 2px; color: #1f2937;">{{invite_code}}</span>
    </div>
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{invite_url}}" style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">接受邀请并注册</a>
    </div>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
    <p style="color: #9ca3af; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p>
</div>
""",
        "default_body_text": "{{inviter_name}} 邀请您加入 TalentMail。邀请码：{{invite_code}}。注册链接：{{invite_url}}",
        "is_system": True,
        "sort_order": 21
    }
]

GLOBAL_VARIABLES = [
    {"key": "app_name", "label": "应用名称", "value": "TalentMail", "value_type": "config", "description": "从 config.json 读取 appName"},
    {"key": "site_url", "label": "网站地址", "value": "", "value_type": "config", "description": "从 config.json 读取"},
    {"key": "support_email", "label": "支持邮箱", "value": "", "value_type": "config", "description": "从 config.json 读取"},
    {"key": "current_year", "label": "当前年份", "value": "", "value_type": "dynamic", "description": "动态计算当前年份"},
    {"key": "current_date", "label": "当前日期", "value": "", "value_type": "dynamic", "description": "动态计算当前日期"},
    {"key": "company_name", "label": "公司名称", "value": "", "value_type": "config", "description": "从 config.json 读取"}
]


def init_template_data(db: Session):
    """初始化模板元数据和全局变量"""
    logger.info("Initializing template metadata and global variables...")
    
    # 1. 初始化全局变量
    for var_data in GLOBAL_VARIABLES:
        existing = db.query(GlobalVariable).filter(GlobalVariable.key == var_data["key"]).first()
        if not existing:
            var = GlobalVariable(
                key=var_data["key"],
                label=var_data["label"],
                value=var_data["value"],
                value_type=var_data["value_type"],
                description=var_data["description"]
            )
            db.add(var)
            logger.info(f"Created global variable: {var_data['key']}")
    
    # 2. 初始化模板元数据
    for meta_data in TEMPLATE_METADATA:
        existing = db.query(TemplateMetadata).filter(TemplateMetadata.code == meta_data["code"]).first()
        if not existing:
            meta = TemplateMetadata(
                code=meta_data["code"],
                name=meta_data["name"],
                category=meta_data["category"],
                description=meta_data["description"],
                trigger_description=meta_data["trigger_description"],
                variables=meta_data["variables"],
                default_subject=meta_data["default_subject"],
                default_body_html=meta_data["default_body_html"],
                default_body_text=meta_data["default_body_text"],
                is_system=meta_data["is_system"],
                sort_order=meta_data["sort_order"]
            )
            db.add(meta)
            logger.info(f"Created template metadata: {meta_data['code']}")
        
        # 3. 确保 system_email_templates 表中有对应的记录（无论元数据是否新建）
        template_existing = db.query(SystemEmailTemplate).filter(SystemEmailTemplate.code == meta_data["code"]).first()
        if not template_existing:
            template = SystemEmailTemplate(
                code=meta_data["code"],
                name=meta_data["name"],
                category=meta_data["category"],
                description=meta_data["description"],
                subject=meta_data["default_subject"],
                body_html=meta_data["default_body_html"],
                body_text=meta_data["default_body_text"],
                variables=[v["key"] for v in meta_data["variables"]],
                is_active=True
            )
            db.add(template)
            logger.info(f"Created system email template: {meta_data['code']}")
    
    # 4. 数据完整性保障：检查 system_email_templates 中是否有未同步到 template_metadata 的记录
    logger.info("Checking for orphaned templates (missing metadata)...")
    all_templates = db.query(SystemEmailTemplate).all()
    
    for template in all_templates:
        metadata_exists = db.query(TemplateMetadata).filter(
            TemplateMetadata.code == template.code
        ).first()
        
        if not metadata_exists:
            logger.warning(f"Found orphaned template without metadata: {template.code}")
            
            # 从模板的 variables 字段构建变量定义
            variables_for_metadata = []
            if template.variables:
                for v in template.variables:
                    if isinstance(v, str):
                        # 旧格式：纯字符串
                        variables_for_metadata.append({
                            "key": v,
                            "label": v,
                            "type": "string",
                            "example": "",
                            "required": False
                        })
                    elif isinstance(v, dict):
                        # 新格式：完整对象
                        variables_for_metadata.append({
                            "key": v.get("key", ""),
                            "label": v.get("label", v.get("key", "")),
                            "type": v.get("type", "string"),
                            "example": v.get("example", ""),
                            "required": v.get("required", False)
                        })
            
            # 创建缺失的元数据记录
            new_metadata = TemplateMetadata(
                code=template.code,
                name=template.name,
                category=template.category,
                description=template.description,
                trigger_description=None,  # 用户创建的模板没有触发描述
                variables=variables_for_metadata,
                default_subject=template.subject,
                default_body_html=template.body_html,
                default_body_text=template.body_text,
                is_system=False,  # 不是系统预设的模板
                sort_order=100  # 排在系统模板后面
            )
            db.add(new_metadata)
            logger.info(f"Created missing metadata for template: {template.code}")
    
    db.commit()
    logger.info("Template data initialization completed.")