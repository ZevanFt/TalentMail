"""邮件解析公共工具模块

从 lmtp_server.py / mail_sync.py / imap_sync.py 中提取的公共函数，
避免三处维护相同逻辑。
"""
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import Optional, List, Tuple


def decode_mime_header(header: Optional[str]) -> str:
    """解码 MIME 编码的邮件头"""
    if not header:
        return ""
    decoded_parts = []
    for part, charset in decode_header(header):
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(charset or 'utf-8', errors='replace'))
        else:
            decoded_parts.append(part)
    return ''.join(decoded_parts)


def parse_email_date(date_str: Optional[str]) -> Optional[datetime]:
    """解析邮件日期字符串，解析失败返回 None"""
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        return None


def extract_email_address(addr: str) -> str:
    """从 'Name <email@domain>' 格式中提取纯邮箱地址（小写）"""
    if '<' in addr and '>' in addr:
        return addr.split('<')[1].split('>')[0].strip().lower()
    return addr.strip().lower()


def get_email_body(msg: email.message.Message) -> Tuple[str, str]:
    """提取邮件正文 (body_text, body_html)，不含附件"""
    body_text, body_html = "", ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                continue
            payload = part.get_payload(decode=True)
            if payload:
                charset = part.get_content_charset() or 'utf-8'
                content = payload.decode(charset, errors='replace')
                if content_type == "text/plain":
                    body_text = content
                elif content_type == "text/html":
                    body_html = content
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or 'utf-8'
            content = payload.decode(charset, errors='replace')
            if msg.get_content_type() == "text/html":
                body_html = content
            else:
                body_text = content
    return body_text, body_html


def get_email_body_and_attachments(msg: email.message.Message) -> Tuple[str, str, List[dict]]:
    """提取邮件正文 (body_html, body_text) 和附件列表

    附件格式: [{"filename": str, "content_type": str, "data": bytes}, ...]
    注意返回顺序: (body_html, body_text, attachments) — 与 LMTP 保持一致
    """
    body_html = ""
    body_text = ""
    attachments: List[dict] = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            filename = part.get_filename()

            if filename:
                filename = decode_mime_header(filename)

            # 附件处理
            if "attachment" in content_disposition or (filename and content_type not in ["text/plain", "text/html"]):
                payload = part.get_payload(decode=True)
                if payload and filename:
                    attachments.append({
                        "filename": filename,
                        "content_type": content_type,
                        "data": payload,
                    })
                continue

            if content_type == "text/html":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or 'utf-8'
                body_html = payload.decode(charset, errors='replace') if payload else ""
            elif content_type == "text/plain":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or 'utf-8'
                body_text = payload.decode(charset, errors='replace') if payload else ""
    else:
        content_type = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        charset = msg.get_content_charset() or 'utf-8'
        content = payload.decode(charset, errors='replace') if payload else ""

        if content_type == "text/html":
            body_html = content
        else:
            body_text = content

    return body_html, body_text, attachments
