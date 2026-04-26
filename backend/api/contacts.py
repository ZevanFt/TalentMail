from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import json
import logging
from db.database import get_db
from api.deps import get_current_user
from db.models.user import User
from db.models.features import Contact
from db.models.email import Email, Folder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contacts", tags=["contacts"])


class ContactCreate(BaseModel):
    name: str
    email: str
    phone: str | None = None
    notes: str | None = None


class ContactUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None


class ContactResponse(BaseModel):
    id: int
    name: str | None
    email: str | None
    phone: str | None
    notes: str | None

    class Config:
        from_attributes = True


class ContactSuggestion(BaseModel):
    name: Optional[str] = None
    email: str
    source: str  # "contact" | "history"


@router.get("/suggestions", response_model=List[ContactSuggestion])
def get_contact_suggestions(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """联系人建议 — 合并已保存联系人 + 已发送邮件历史收件人"""
    seen_emails: set[str] = set()
    results: list[dict] = []

    # 1. 已保存联系人（优先）
    contacts = db.query(Contact).filter(
        Contact.owner_id == user.id,
        (Contact.name.ilike(f"%{q}%")) | (Contact.email.ilike(f"%{q}%"))
    ).limit(10).all()

    for c in contacts:
        if c.email and c.email.lower() not in seen_emails:
            seen_emails.add(c.email.lower())
            results.append({"name": c.name, "email": c.email, "source": "contact"})

    # 2. 已发送邮件的收件人（补充）
    if len(results) < 10:
        sent_folder = db.query(Folder).filter(
            Folder.user_id == user.id, Folder.role == "sent"
        ).first()
        if sent_folder:
            sent_emails = db.query(Email.recipients).filter(
                Email.folder_id == sent_folder.id,
                Email.recipients.ilike(f"%{q}%")
            ).order_by(Email.sent_at.desc()).limit(50).all()

            for (recipients_raw,) in sent_emails:
                if not recipients_raw:
                    continue
                # recipients 可能是 JSON 或逗号分隔文本
                addrs = _extract_emails_from_recipients(recipients_raw)
                for addr in addrs:
                    if addr.lower() in seen_emails:
                        continue
                    if q.lower() in addr.lower():
                        seen_emails.add(addr.lower())
                        results.append({"name": None, "email": addr, "source": "history"})
                        if len(results) >= 10:
                            break
                if len(results) >= 10:
                    break

    return results


def _extract_emails_from_recipients(raw: str) -> list[str]:
    """从 recipients 字段提取邮箱地址（兼容 JSON 和逗号分隔格式）"""
    emails = []
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            for key in ("to", "cc", "bcc"):
                for item in data.get(key, []):
                    if isinstance(item, dict) and item.get("email"):
                        emails.append(item["email"])
                    elif isinstance(item, str):
                        emails.append(item)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("email"):
                    emails.append(item["email"])
                elif isinstance(item, str):
                    emails.append(item)
    except (json.JSONDecodeError, TypeError):
        # 逗号分隔文本
        for part in raw.split(","):
            addr = part.strip()
            if "<" in addr and ">" in addr:
                addr = addr.split("<")[1].split(">")[0].strip()
            if "@" in addr:
                emails.append(addr)
    return emails


class ContactListResponse(BaseModel):
    items: List[ContactResponse]
    total: int
    page: int
    limit: int


@router.get("", response_model=ContactListResponse)
def get_contacts(
    q: str = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Contact).filter(Contact.owner_id == user.id)
    if q:
        query = query.filter((Contact.name.ilike(f"%{q}%")) | (Contact.email.ilike(f"%{q}%")))
    total = query.count()
    items = query.order_by(Contact.name).offset((page - 1) * limit).limit(limit).all()
    return ContactListResponse(items=items, total=total, page=page, limit=limit)


@router.post("", response_model=ContactResponse)
def create_contact(data: ContactCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    contact = Contact(owner_id=user.id, name=data.name, email=data.email, phone=data.phone, notes=data.notes)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: int, data: ContactUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.owner_id == user.id).first()
    if not contact:
        raise HTTPException(404, "联系人不存在")
    if data.name is not None:
        contact.name = data.name
    if data.email is not None:
        contact.email = data.email
    if data.phone is not None:
        contact.phone = data.phone
    if data.notes is not None:
        contact.notes = data.notes
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.owner_id == user.id).first()
    if not contact:
        raise HTTPException(404, "联系人不存在")
    db.delete(contact)
    db.commit()
    return {"message": "删除成功"}