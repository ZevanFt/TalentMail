from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from db.database import get_db
from api.deps import get_current_user
from db.models.user import User
from db.models.features import Contact

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


@router.get("", response_model=List[ContactResponse])
def get_contacts(q: str = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Contact).filter(Contact.owner_id == user.id)
    if q:
        query = query.filter((Contact.name.ilike(f"%{q}%")) | (Contact.email.ilike(f"%{q}%")))
    return query.order_by(Contact.name).all()


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