from sqlalchemy.orm import Session
from db import models

def get_user_folder_by_role(db: Session, user_id: int, role: str) -> models.Folder:
    """
    Retrieves a user's folder by its special role (e.g., 'sent', 'inbox').
    """
    return db.query(models.Folder).filter(
        models.Folder.user_id == user_id,
        models.Folder.role == role
    ).first()