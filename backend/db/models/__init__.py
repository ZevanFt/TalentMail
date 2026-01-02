# Import the Base from database setup, so all models can inherit from it
from db.database import Base

# Import all models to make them accessible via this package.
from .user import User, UserSession, PoolActivityLog, BlockedSender
from .email import Folder, Email, Attachment, Signature, Alias, TempMailbox, Domain
from .billing import Plan, Subscription, Transaction, RedemptionCode, InviteCode, InviteCodeUsage, SubscriptionHistory
from .features import Contact, Filter, Template, Tag, EmailTag, TrackingPixel, TrackingEvent
from .system import ServerLog, ApiKey, ReservedPrefix, SystemEmailTemplate, VerificationCode
from .external_account import ExternalAccount
from .drive import DriveFile
from .template import TemplateMetadata, GlobalVariable
from .automation import AutomationRule, AutomationLog

# It's also a good practice to define __all__ to specify what gets imported
# when a client does `from .models import *`
__all__ = [
    "Base",
    "User",
    "UserSession",
    "PoolActivityLog",
    "BlockedSender",
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
    "InviteCodeUsage",
    "SubscriptionHistory",
    "Contact",
    "Filter",
    "Template",
    "Tag",
    "EmailTag",
    "TrackingPixel",
    "TrackingEvent",
    "ServerLog",
    "ApiKey",
    "ReservedPrefix",
    "SystemEmailTemplate",
    "VerificationCode",
    "ExternalAccount",
    "DriveFile",
    "TemplateMetadata",
    "GlobalVariable",
    "AutomationRule",
    "AutomationLog",
]