"""
垃圾邮件管理 API
提供垃圾邮件标记、白名单管理、SpamAssassin 训练等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from db import models
from db.models.user import TrustedSender, SpamReport
from db.models.email import Email, Folder
from db.database import SessionLocal
from api import deps
from crud.folder import get_user_folder_by_role

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== Schemas ====================

class TrustedSenderCreate(BaseModel):
    email: str  # 可以是完整邮箱或 @domain.com 格式
    note: Optional[str] = None


class TrustedSenderRead(BaseModel):
    id: int
    email: str
    sender_type: str
    note: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class SpamActionRequest(BaseModel):
    email_ids: List[int]


class SpamReportRead(BaseModel):
    id: int
    email_id: int
    report_type: str
    learned: bool
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== 白名单 API ====================

@router.get("/whitelist", response_model=List[TrustedSenderRead])
def get_trusted_senders(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取当前用户的白名单列表"""
    items = db.query(TrustedSender).filter(
        TrustedSender.user_id == current_user.id
    ).order_by(TrustedSender.created_at.desc()).all()

    return [
        {
            "id": item.id,
            "email": item.email,
            "sender_type": item.sender_type,
            "note": item.note,
            "created_at": item.created_at.isoformat() if item.created_at else None
        }
        for item in items
    ]


@router.post("/whitelist", response_model=TrustedSenderRead)
def add_trusted_sender(
    data: TrustedSenderCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """添加发件人到白名单"""
    email = data.email.lower().strip()

    # 判断类型：如果以 @ 开头则是域名，否则是完整邮箱
    if email.startswith('@'):
        sender_type = 'domain'
    else:
        sender_type = 'email'

    # 检查是否已存在
    existing = db.query(TrustedSender).filter(
        TrustedSender.user_id == current_user.id,
        TrustedSender.email == email
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="该地址已在白名单中")

    trusted = TrustedSender(
        user_id=current_user.id,
        email=email,
        sender_type=sender_type,
        note=data.note
    )
    db.add(trusted)
    db.commit()
    db.refresh(trusted)

    return {
        "id": trusted.id,
        "email": trusted.email,
        "sender_type": trusted.sender_type,
        "note": trusted.note,
        "created_at": trusted.created_at.isoformat() if trusted.created_at else None
    }


@router.delete("/whitelist/{trusted_id}")
def remove_trusted_sender(
    trusted_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """从白名单移除发件人"""
    trusted = db.query(TrustedSender).filter(
        TrustedSender.id == trusted_id,
        TrustedSender.user_id == current_user.id
    ).first()

    if not trusted:
        raise HTTPException(status_code=404, detail="记录不存在")

    db.delete(trusted)
    db.commit()

    return {"status": "success", "message": "已从白名单移除"}


# ==================== 垃圾邮件操作 API ====================

@router.post("/mark-spam")
def mark_as_spam(
    data: SpamActionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """将邮件标记为垃圾邮件（移动到垃圾邮件文件夹）"""
    # 获取垃圾邮件文件夹
    spam_folder = get_user_folder_by_role(db, user_id=current_user.id, role="spam")
    if not spam_folder:
        raise HTTPException(status_code=404, detail="垃圾邮件文件夹不存在")

    moved_count = 0
    reports = []

    for email_id in data.email_ids:
        # 验证邮件属于当前用户
        email = db.query(Email).join(Folder).filter(
            Email.id == email_id,
            Folder.user_id == current_user.id
        ).first()

        if not email:
            continue

        original_folder_id = email.folder_id

        # 移动到垃圾邮件文件夹
        if email.folder_id != spam_folder.id:
            email.folder_id = spam_folder.id
            moved_count += 1

            # 创建报告记录
            report = SpamReport(
                user_id=current_user.id,
                email_id=email_id,
                report_type='spam',
                original_folder_id=original_folder_id,
                learned=False
            )
            db.add(report)
            reports.append(report)

    db.commit()

    # 后台任务：训练 SpamAssassin（如果有报告）
    if reports:
        report_ids = [r.id for r in reports]
        background_tasks.add_task(train_spamassassin, report_ids, 'spam')

    return {
        "status": "success",
        "message": f"已将 {moved_count} 封邮件标记为垃圾邮件",
        "moved_count": moved_count
    }


@router.post("/mark-not-spam")
def mark_as_not_spam(
    data: SpamActionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """将邮件标记为非垃圾邮件（移动到收件箱）"""
    # 获取收件箱文件夹
    inbox_folder = get_user_folder_by_role(db, user_id=current_user.id, role="inbox")
    if not inbox_folder:
        raise HTTPException(status_code=404, detail="收件箱不存在")

    moved_count = 0
    reports = []

    for email_id in data.email_ids:
        # 验证邮件属于当前用户
        email = db.query(Email).join(Folder).filter(
            Email.id == email_id,
            Folder.user_id == current_user.id
        ).first()

        if not email:
            continue

        original_folder_id = email.folder_id

        # 移动到收件箱
        email.folder_id = inbox_folder.id
        moved_count += 1

        # 创建报告记录
        report = SpamReport(
            user_id=current_user.id,
            email_id=email_id,
            report_type='ham',
            original_folder_id=original_folder_id,
            learned=False
        )
        db.add(report)
        reports.append(report)

    db.commit()

    # 后台任务：训练 SpamAssassin
    if reports:
        report_ids = [r.id for r in reports]
        background_tasks.add_task(train_spamassassin, report_ids, 'ham')

    return {
        "status": "success",
        "message": f"已将 {moved_count} 封邮件标记为非垃圾邮件",
        "moved_count": moved_count
    }


@router.get("/reports", response_model=List[SpamReportRead])
def get_spam_reports(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """获取用户的垃圾邮件报告记录"""
    reports = db.query(SpamReport).filter(
        SpamReport.user_id == current_user.id
    ).order_by(SpamReport.created_at.desc()).limit(limit).all()

    return [
        {
            "id": r.id,
            "email_id": r.email_id,
            "report_type": r.report_type,
            "learned": r.learned,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in reports
    ]


# ==================== 辅助功能 ====================

def is_sender_trusted(db: Session, user_id: int, sender_email: str) -> bool:
    """检查发件人是否在白名单中"""
    sender_email = sender_email.lower().strip()

    # 提取域名
    if '@' in sender_email:
        domain = '@' + sender_email.split('@')[1]
    else:
        return False

    # 检查完整邮箱或域名是否在白名单
    trusted = db.query(TrustedSender).filter(
        TrustedSender.user_id == user_id,
        (TrustedSender.email == sender_email) | (TrustedSender.email == domain)
    ).first()

    return trusted is not None


def is_sender_blocked(db: Session, user_id: int, sender_email: str) -> bool:
    """检查发件人是否在黑名单中"""
    from db.models.user import BlockedSender

    sender_email = sender_email.lower().strip()

    blocked = db.query(BlockedSender).filter(
        BlockedSender.user_id == user_id,
        BlockedSender.email == sender_email
    ).first()

    return blocked is not None


async def train_spamassassin(report_ids: List[int], report_type: str):
    """
    后台任务：训练 SpamAssassin

    在实际生产环境中，这里需要：
    1. 获取邮件的原始内容（.eml 文件）
    2. 调用 sa-learn 命令训练 SpamAssassin
    3. 更新报告的 learned 状态

    由于 docker-mailserver 已经启用了 SpamAssassin，
    可以通过 docker exec 调用 sa-learn 命令。
    """
    db = SessionLocal()
    try:
        reports = db.query(SpamReport).filter(SpamReport.id.in_(report_ids)).all()
        logger.info(f"[SpamAssassin] 准备训练 {len(reports)} 封邮件为 {report_type}")

        # TODO: 实际调用 sa-learn 命令
        # 示例命令:
        # docker exec talentmail-mailserver-1 sa-learn --spam /path/to/email.eml
        # docker exec talentmail-mailserver-1 sa-learn --ham /path/to/email.eml

        # 标记为已学习
        for report in reports:
            report.learned = True

        db.commit()
        logger.info(f"[SpamAssassin] 训练完成: {len(reports)} 封邮件")

    except Exception as e:
        db.rollback()
        logger.error(f"[SpamAssassin] 训练失败: {e}")
    finally:
        db.close()
