"""邮件批量导入 API — 支持 .eml 和 .mbox 文件"""
import email
import mailbox
import os
import uuid
import tempfile
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db.database import get_db
from api.deps import get_current_user
from db.models.user import User
from db.models.email import Email, Folder, Attachment
from core.email_parser import (
    decode_mime_header,
    parse_email_date,
    extract_email_address,
    get_email_body_and_attachments,
)
from utils.rate_limit import SlidingWindowLimiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/emails", tags=["Email Import"])

# 限速: 每用户每 5 分钟最多 5 次
_import_limiter = SlidingWindowLimiter(max_attempts=5, window_seconds=300)

MAX_IMPORT_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_EMAILS_PER_MBOX = 500
ATTACHMENT_DIR = "/app/uploads/attachments"
os.makedirs(ATTACHMENT_DIR, exist_ok=True)


class ImportResult(BaseModel):
    total_found: int
    imported: int
    skipped_duplicate: int
    skipped_error: int
    errors: list[str]


def _get_user_inbox(db: Session, user_id: int, target_folder_id: Optional[int]) -> Folder:
    """获取目标文件夹，默认为收件箱"""
    if target_folder_id:
        folder = db.query(Folder).filter(
            Folder.id == target_folder_id,
            Folder.user_id == user_id,
        ).first()
        if folder:
            return folder

    # 默认使用 inbox
    inbox = db.query(Folder).filter(
        Folder.user_id == user_id,
        Folder.role == "inbox",
    ).first()
    if not inbox:
        raise HTTPException(500, "找不到收件箱文件夹")
    return inbox


def _import_single_email(
    db: Session,
    msg: email.message.Message,
    user: User,
    folder: Folder,
    errors: list[str],
) -> str:
    """导入单封邮件，返回 'imported' | 'duplicate' | 'error'"""
    try:
        message_id = msg.get("Message-ID", "").strip()
        subject = decode_mime_header(msg.get("Subject", ""))
        sender = decode_mime_header(msg.get("From", ""))
        recipients = decode_mime_header(msg.get("To", ""))
        date_str = msg.get("Date")
        received_at = parse_email_date(date_str) or datetime.now(timezone.utc)
        in_reply_to = msg.get("In-Reply-To", "")
        references_raw = msg.get("References", "")

        # 按 message_id 去重（同用户）
        if message_id:
            existing = db.query(Email.id).join(Folder).filter(
                Email.message_id == message_id,
                Folder.user_id == user.id,
            ).first()
            if existing:
                return "duplicate"

        # 解析正文和附件
        body_html, body_text, raw_attachments = get_email_body_and_attachments(msg)

        # 创建邮件记录
        email_obj = Email(
            folder_id=folder.id,
            mailbox_address=user.email,
            message_id=message_id or f"<imported-{uuid.uuid4().hex}@talentmail>",
            subject=subject or "(无主题)",
            sender=sender,
            recipients=recipients,
            body_text=body_text,
            body_html=body_html,
            received_at=received_at,
            is_read=True,
            delivery_status="imported",
            in_reply_to=in_reply_to or None,
            references=references_raw or None,
        )
        db.add(email_obj)
        db.flush()  # 获取 email_obj.id

        # 保存附件
        for att_data in raw_attachments:
            att_filename = att_data.get("filename", "attachment")
            att_content_type = att_data.get("content_type", "application/octet-stream")
            att_bytes = att_data.get("data", b"")

            ext = os.path.splitext(att_filename)[1] if att_filename else ""
            unique_name = f"{uuid.uuid4().hex}{ext}"
            file_path = os.path.join(ATTACHMENT_DIR, unique_name)

            with open(file_path, "wb") as f:
                f.write(att_bytes)

            attachment = Attachment(
                email_id=email_obj.id,
                user_id=user.id,
                filename=att_filename,
                content_type=att_content_type,
                size=len(att_bytes),
                file_path=file_path,
            )
            db.add(attachment)

        return "imported"

    except Exception as e:
        logger.warning(f"导入邮件失败: {e}", exc_info=True)
        subject_hint = decode_mime_header(msg.get("Subject", ""))[:50] if msg else "?"
        errors.append(f"「{subject_hint}」: {str(e)[:100]}")
        return "error"


@router.post("/import", response_model=ImportResult)
async def import_emails(
    file: UploadFile = File(...),
    folder_id: Optional[int] = Query(None, description="目标文件夹ID（默认收件箱）"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """导入 .eml 或 .mbox 文件中的邮件"""
    if not _import_limiter.allow(f"import:{user.id}"):
        raise HTTPException(429, "导入过于频繁，请 5 分钟后再试")

    filename = (file.filename or "").lower()
    if not filename.endswith((".eml", ".mbox")):
        raise HTTPException(400, "仅支持 .eml 和 .mbox 格式")

    # 读取文件内容
    content = await file.read()
    if len(content) > MAX_IMPORT_FILE_SIZE:
        raise HTTPException(413, f"文件大小超过限制 ({MAX_IMPORT_FILE_SIZE // 1024 // 1024}MB)")

    folder = _get_user_inbox(db, user.id, folder_id)

    total_found = 0
    imported = 0
    skipped_duplicate = 0
    skipped_error = 0
    errors: list[str] = []

    if filename.endswith(".eml"):
        # 单封 .eml
        total_found = 1
        msg = email.message_from_bytes(content)
        result = _import_single_email(db, msg, user, folder, errors)
        if result == "imported":
            imported = 1
        elif result == "duplicate":
            skipped_duplicate = 1
        else:
            skipped_error = 1

    elif filename.endswith(".mbox"):
        # .mbox 文件（可能包含多封邮件）
        # mailbox.mbox 需要文件路径，写入临时文件
        with tempfile.NamedTemporaryFile(suffix=".mbox", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            mbox = mailbox.mbox(tmp_path)
            messages = list(mbox)
            total_found = len(messages)

            if total_found > MAX_EMAILS_PER_MBOX:
                raise HTTPException(400, f"mbox 文件包含 {total_found} 封邮件，超过单次导入上限 ({MAX_EMAILS_PER_MBOX})")

            for msg in messages:
                result = _import_single_email(db, msg, user, folder, errors)
                if result == "imported":
                    imported += 1
                elif result == "duplicate":
                    skipped_duplicate += 1
                else:
                    skipped_error += 1

            mbox.close()
        finally:
            os.unlink(tmp_path)

    db.commit()
    logger.info(f"用户 {user.id} 导入邮件: 找到 {total_found}, 导入 {imported}, 跳过重复 {skipped_duplicate}, 错误 {skipped_error}")

    return ImportResult(
        total_found=total_found,
        imported=imported,
        skipped_duplicate=skipped_duplicate,
        skipped_error=skipped_error,
        errors=errors[:20],  # 最多返回 20 条错误
    )
