import logging
from sqlalchemy.orm import Session
from crud import user as crud_user
from schemas import schemas
from core.config import settings
from db.database import engine, SessionLocal
from db import models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db() -> None:
    """
    Initializes the database. Creates tables and the initial admin user.
    Manages its own database session to avoid conflicts.
    """
    db = SessionLocal()
    try:
        logger.info("Creating all tables...")
        models.Base.metadata.create_all(bind=engine)
        logger.info("Tables created.")
        _create_initial_admin(db)
        _ensure_default_folders_for_all_users(db) # Add this line
        db.commit() # Commit the changes
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
        logger.info("Database session closed after initialization.")


def _create_initial_admin(db: Session) -> None:
    """
    Creates the initial admin user if it doesn't exist.
    Ensures the admin user has the 'admin' role with all permissions.
    """
    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.ADMIN_PASSWORD

    user = crud_user.get_user_by_email(db, email=admin_email)
    if not user:
        user_in = schemas.UserCreate(
            email=admin_email,
            password=admin_password,
            display_name="Admin",
            phone=None,
            redemption_code="ADMIN_CODE"
        )
        user = crud_user.create_user(db, user=user_in)
        if user:
            # Set admin role for the newly created user
            user.role = "admin"
            db.add(user)
            logger.info(f"Initial admin user created with admin role: {admin_email}")
        else:
            logger.error(f"Failed to create initial admin user: {admin_email}")
    else:
        # Ensure existing admin user has admin role
        if user.role != "admin":
            user.role = "admin"
            db.add(user)
            logger.info(f"Updated existing user {admin_email} to admin role.")
        else:
            logger.info(f"Admin user {admin_email} already exists with admin role. Skipping.")


def _ensure_default_folders_for_all_users(db: Session) -> None:
    """
    Checks all users and creates default folders for those who don't have them.
    This is useful for applying the folder structure to existing users.
    """
    logger.info("Checking for users missing default folders...")
    users = db.query(models.User).all()
    for user in users:
        # A simple way to check is to see if they have an 'inbox' folder.
        inbox_folder = crud_user.get_folder_by_role(db, user_id=user.id, role="inbox")
        if not inbox_folder:
            logger.info(f"User {user.email} (ID: {user.id}) is missing default folders. Creating them now...")
            try:
                crud_user.create_default_folders_for_user(db, user_id=user.id)
                logger.info(f"Successfully added folder creation tasks for user {user.email}.")
            except Exception as e:
                logger.error(f"Failed to create folders for user {user.email}: {e}", exc_info=True)
                # We will let the main exception handler catch this and rollback.
                raise
        else:
            logger.info(f"User {user.email} already has an inbox. Assuming all folders are present.")
    logger.info("Folder check for all users complete.")
