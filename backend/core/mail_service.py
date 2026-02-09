"""
邮件发送服务 - 统一入口
负责调用 TemplateEngine 渲染模板，并调用底层 SMTP 发送邮件
"""
import smtplib
import logging
from typing import Dict, Any, Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid
from sqlalchemy.orm import Session

from core.config import settings
from core.template_engine import TemplateEngine

logger = logging.getLogger(__name__)


class MailService:
    def __init__(self, db: Session):
        self.db = db
        self.template_engine = TemplateEngine(db)

    def send_by_template(
        self,
        template_code: str,
        to_email: str,
        context: Dict[str, Any],
        from_email: Optional[str] = None,
        cc: Optional[List[str]] = None
    ) -> bool:
        """
        通过模板发送邮件
        
        Args:
            template_code: 模板代码
            to_email: 收件人邮箱
            context: 模板变量上下文
            from_email: 发件人邮箱（可选）
            cc: 抄送列表（可选）
        """
        # 渲染模板
        rendered = self.template_engine.render_template(template_code, context)
        
        if not rendered:
            logger.error(f"Template not found or inactive: {template_code}")
            return False
            
        return self.send_raw(
            to_email=to_email,
            subject=rendered["subject"],
            body_html=rendered["body_html"],
            body_text=rendered["body_text"],
            from_email=from_email,
            cc=cc
        )

    def send_raw(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_email: Optional[str] = None,
        cc: Optional[List[str]] = None
    ) -> bool:
        """
        直接发送邮件 (不使用模板)
        
        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            body_html: HTML 正文
            body_text: 纯文本正文（可选）
            from_email: 发件人邮箱（可选）
            cc: 抄送列表（可选）
        """
        server = None
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')

            # 确定发件人
            if not from_email:
                from_email = f"noreply@{settings.BASE_DOMAIN}"
                sender_name = settings.APP_NAME
            else:
                sender_name = from_email.split('@')[0]

            msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), from_email))
            msg['To'] = to_email
            msg['Subject'] = Header(subject, 'utf-8')
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid(domain=settings.BASE_DOMAIN)

            # 添加抄送
            if cc:
                msg['Cc'] = ', '.join(cc)

            # 添加内容
            if body_text:
                msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

            if body_html:
                msg.attach(MIMEText(body_html, 'html', 'utf-8'))
            elif not body_text:
                # 如果既没有 HTML 也没有纯文本，添加一个空的 HTML 部分以避免错误
                msg.attach(MIMEText("", 'html', 'utf-8'))

            # 发送
            server = smtplib.SMTP(settings.MAIL_SERVER, settings.SMTP_PORT, timeout=30)

            if settings.MAIL_STARTTLS:
                server.starttls()

            if settings.USE_CREDENTIALS:
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)

            # SMTP envelope sender
            envelope_from = settings.MAIL_USERNAME if settings.USE_CREDENTIALS else from_email

            # 所有收件人（包括抄送）
            all_recipients = [to_email]
            if cc:
                all_recipients.extend(cc)

            server.sendmail(envelope_from, all_recipients, msg.as_string())

            logger.info(f"Email sent to {to_email}, subject: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
            return False
        finally:
            if server:
                try:
                    server.quit()
                except:
                    pass