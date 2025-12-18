from sqlalchemy.orm import Session
from db import models
from schemas import email as email_schema
import json
from typing import Optional

def create_email(
    db: Session,
    email: email_schema.EmailCreate,
    sender_email: str,
    user_id: int,
    folder_id: int,
    in_reply_to: Optional[str] = None,
    references: Optional[str] = None,
    thread_id: Optional[str] = None
) -> models.Email:
    """
    Creates a new email record in the database.
    Note: This function only saves the email to the DB, it does not send it.
    """
    # Convert recipient lists to a simple JSON string for storage
    recipients_dict = {
        "to": [recipient.model_dump() for recipient in email.to],
        "cc": [recipient.model_dump() for recipient in email.cc],
        "bcc": [recipient.model_dump() for recipient in email.bcc],
    }
    recipients_str = json.dumps(recipients_dict)

    db_email = models.Email(
        folder_id=folder_id,
        mailbox_address=sender_email,
        message_id=None,  # This will be updated after sending with the real Message-ID
        in_reply_to=in_reply_to,
        references=references,
        thread_id=thread_id,
        subject=email.subject,
        sender=sender_email,
        recipients=recipients_str,
        body_html=email.body_html,
        body_text=email.body_text,
        is_draft=False,
        is_read=True,
        is_tracked=email.is_tracked,
    )
    db.add(db_email)
    db.commit()
    db.refresh(db_email)
    return db_email