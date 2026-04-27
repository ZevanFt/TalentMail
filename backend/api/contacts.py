from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
import csv
import io
import re
import json
import logging
from db.database import get_db
from api.deps import get_current_user
from db.models.user import User
from db.models.features import Contact
from db.models.email import Email, Folder
from utils.db import escape_like

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contacts", tags=["contacts"])


class ContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=3, max_length=320)  # RFC 5321
    phone: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=2000)


class ContactUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: str | None = Field(default=None, min_length=3, max_length=320)
    phone: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=2000)


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
        (Contact.name.ilike(f"%{escape_like(q)}%")) | (Contact.email.ilike(f"%{escape_like(q)}%"))
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
                Email.recipients.ilike(f"%{escape_like(q)}%")
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
        query = query.filter((Contact.name.ilike(f"%{escape_like(q)}%")) | (Contact.email.ilike(f"%{escape_like(q)}%")))
    total = query.count()
    items = query.order_by(Contact.name).offset((page - 1) * limit).limit(limit).all()
    return ContactListResponse(items=items, total=total, page=page, limit=limit)


@router.post("", response_model=ContactResponse)
def create_contact(data: ContactCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # 检查同用户下是否已存在相同 email 的联系人
    if data.email:
        existing = db.query(Contact).filter(
            Contact.owner_id == user.id,
            Contact.email == data.email.strip().lower()
        ).first()
        if existing:
            raise HTTPException(400, f"联系人邮箱 {data.email} 已存在")
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
    return {"status": "success", "message": "删除成功"}


# =============================================================================
# 导入/导出
# =============================================================================

@router.get("/export")
def export_contacts(
    format: str = Query("csv", pattern="^(csv|vcf)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """导出联系人为 CSV 或 vCard 格式"""
    contacts = db.query(Contact).filter(Contact.owner_id == user.id).order_by(Contact.name).all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Name", "Email", "Phone", "Notes"])
        for c in contacts:
            writer.writerow([c.name or "", c.email or "", c.phone or "", c.notes or ""])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=contacts.csv"},
        )
    else:  # vcf
        lines = []
        for c in contacts:
            lines.append("BEGIN:VCARD")
            lines.append("VERSION:3.0")
            if c.name:
                lines.append(f"FN:{c.name}")
                # 简单拆分：取最后一个空格分 family/given
                parts = c.name.rsplit(" ", 1)
                if len(parts) == 2:
                    lines.append(f"N:{parts[1]};{parts[0]};;;")
                else:
                    lines.append(f"N:{c.name};;;;")
            if c.email:
                lines.append(f"EMAIL;TYPE=INTERNET:{c.email}")
            if c.phone:
                lines.append(f"TEL;TYPE=CELL:{c.phone}")
            if c.notes:
                # vCard NOTE 字段需转义换行
                safe_notes = c.notes.replace("\n", "\\n").replace(",", "\\,")
                lines.append(f"NOTE:{safe_notes}")
            lines.append("END:VCARD")
            lines.append("")
        vcf_content = "\r\n".join(lines)
        return StreamingResponse(
            iter([vcf_content]),
            media_type="text/vcard",
            headers={"Content-Disposition": "attachment; filename=contacts.vcf"},
        )


@router.post("/import")
async def import_contacts(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """导入联系人（CSV 或 vCard 格式，自动检测）

    限制：最大 1MB，最多 1000 条。
    """
    # 文件大小限制
    content = await file.read()
    if len(content) > 1_048_576:  # 1MB
        raise HTTPException(400, "文件过大，最大 1MB")

    text = content.decode("utf-8", errors="replace")

    # 自动检测格式
    if "BEGIN:VCARD" in text.upper():
        contacts_data = _parse_vcf(text)
    else:
        contacts_data = _parse_csv(text)

    if len(contacts_data) > 1000:
        raise HTTPException(400, "联系人数量超过 1000 条上限")

    # 获取已有邮箱（去重用）
    existing_emails = set(
        row[0].lower() for row in
        db.query(Contact.email).filter(
            Contact.owner_id == user.id,
            Contact.email.isnot(None)
        ).all()
        if row[0]
    )

    imported = 0
    skipped = 0
    errors = []

    for i, item in enumerate(contacts_data):
        email_addr = (item.get("email") or "").strip().lower()
        if not email_addr or "@" not in email_addr:
            errors.append(f"第 {i + 1} 行: 无效邮箱")
            continue
        if email_addr in existing_emails:
            skipped += 1
            continue

        name = (item.get("name") or "").strip()[:200]
        phone = (item.get("phone") or "").strip()[:50] or None
        notes = (item.get("notes") or "").strip()[:2000] or None

        contact = Contact(
            owner_id=user.id,
            name=name or email_addr.split("@")[0],
            email=email_addr,
            phone=phone,
            notes=notes,
        )
        db.add(contact)
        existing_emails.add(email_addr)
        imported += 1

    if imported > 0:
        db.commit()

    return {
        "status": "success",
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:20],  # 最多返回 20 条错误
    }


def _parse_csv(text: str) -> list[dict]:
    """解析 CSV 文本，自动映射列名"""
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return []

    # 模糊匹配列名
    field_map = {}
    for fn in reader.fieldnames:
        fn_lower = fn.strip().lower()
        if fn_lower in ("name", "姓名", "full name", "fullname", "display name"):
            field_map["name"] = fn
        elif fn_lower in ("email", "邮箱", "e-mail", "email address", "电子邮件"):
            field_map["email"] = fn
        elif fn_lower in ("phone", "电话", "tel", "telephone", "mobile", "手机"):
            field_map["phone"] = fn
        elif fn_lower in ("notes", "备注", "note", "comment", "description"):
            field_map["notes"] = fn

    results = []
    for row in reader:
        item = {
            "name": row.get(field_map.get("name", ""), ""),
            "email": row.get(field_map.get("email", ""), ""),
            "phone": row.get(field_map.get("phone", ""), ""),
            "notes": row.get(field_map.get("notes", ""), ""),
        }
        if item["email"]:
            results.append(item)
    return results


def _parse_vcf(text: str) -> list[dict]:
    """解析 vCard 文本"""
    results = []
    current: dict | None = None

    for line in text.splitlines():
        line = line.strip()
        if line.upper() == "BEGIN:VCARD":
            current = {"name": "", "email": "", "phone": "", "notes": ""}
        elif line.upper() == "END:VCARD":
            if current and current.get("email"):
                results.append(current)
            current = None
        elif current is not None:
            if line.upper().startswith("FN:"):
                current["name"] = line[3:].strip()
            elif "EMAIL" in line.upper() and ":" in line:
                current["email"] = line.split(":", 1)[1].strip()
            elif "TEL" in line.upper() and ":" in line:
                current["phone"] = line.split(":", 1)[1].strip()
            elif line.upper().startswith("NOTE:"):
                current["notes"] = line[5:].replace("\\n", "\n").replace("\\,", ",").strip()

    return results