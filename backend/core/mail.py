import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid
from schemas import email as email_schema
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_email(
    email_data: email_schema.EmailCreate,
    sender_email: str,
):
    """
    Connects to the SMTP server and sends an email.
    """
    # Create the email message (multipart/alternative for text + html)
    msg = MIMEMultipart('alternative')
    
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
    
    msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
    msg.attach(MIMEText(body_html, 'html', 'utf-8'))

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
