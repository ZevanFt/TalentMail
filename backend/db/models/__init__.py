# Import the Base from database setup, so all models can inherit from it
from db.database import Base

# Import all models to make them accessible via this package.
from .user import User, UserSession, PoolActivityLog
from .email import Folder, Email, Attachment, Signature, Alias, TempMailbox, Domain
from .billing import Plan, Subscription, Transaction, RedemptionCode, InviteCode
from .features import Contact, Filter, Template, Tag, EmailTag, TrackingPixel, TrackingEvent
from .system import ServerLog, ApiKey

# It's also a good practice to define __all__ to specify what gets imported
# when a client does `from .models import *`
__all__ = [
    "Base",
    "User",
    "UserSession",
    "PoolActivityLog",
    "Folder",
    "Email",
    "Attachment",
    "Signature",
    "Alias",
    "TempMailbox",
    "Domain",
    "Plan",
    "Subscription",
    "Transaction",
    "RedemptionCode",
    "InviteCode",
    "Contact",
    "Filter",
    "Template",
    "Tag",
    "EmailTag",
    "TrackingPixel",
    "TrackingEvent",
    "ServerLog",
    "ApiKey",
]