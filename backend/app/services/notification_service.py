from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.enums import NotificationStatus, NotificationType, ResourceStatus
from app.models.notification import Notification
from app.models.recurring_expense_rule import RecurringExpenseRule
from app.models.resource_account import ResourceAccount
from app.models.resource_allocation import ResourceAllocation
from app.permissions.dependencies import CurrentUser
from app.permissions.resource_scope import can_read_resource, readable_resources
from app.schemas.enterprise import NotificationListResponse, NotificationPublic
from app.services.settings_service import business_today, get_expiring_days


def _now():
    return datetime.now(timezone.utc)


def _serialize(item: Notification) -> NotificationPublic:
    resource = item.resource_account
    project = item.project
    return NotificationPublic(
        id=item.id,
        type=item.type,
        target_type=item.target_type,
        target_id=item.target_id,
        title=item.title,
        message=item.message,
        status=item.status,
        resource_account_id=item.resource_account_id,
        resource_name=resource.resource_name if resource else None,
        project_id=item.project_id,
        project_name=project.name if project else None,
        due_date=item.due_date.isoformat() if item.due_date else None,
        created_at=item.created_at,
        read_at=item.read_at,
        resolved_at=item.resolved_at,
    )


def _existing(db: Session, ntype: str, target_type: str, target_id: str, period_key: str) -> Notification | None:
    return (
        db.query(Notification)
        .filter(
            Notification.type == ntype,
            Notification.target_type == target_type,
            Notification.target_id == target_id,
            Notification.period_key == period_key,
        )
        .first()
    )


def _create_if_absent(
    db: Session,
    *,
    ntype: str,
    target_type: str,
    target_id: str,
    period_key: str,
    title: str,
    message: str,
    resource_account_id: int | None = None,
    project_id: int | None = None,
    due_date=None,
) -> bool:
    if _existing(db, ntype, target_type, target_id, period_key):
        return False
    db.add(
        Notification(
            type=ntype,
            target_type=target_type,
            target_id=str(target_id),
            period_key=period_key,
            title=title,
            message=message,
            status=NotificationStatus.UNREAD.value,
            resource_account_id=resource_account_id,
            project_id=project_id,
            due_date=due_date,
        )
    )
    return True


def generate_notifications(db: Session) -> int:
    today = business_today(db)
    days = get_expiring_days(db)
    period_key = today.isoformat()
    created = 0

    resources = db.query(ResourceAccount).all()
    for account in resources:
        active_count = (
            db.query(ResourceAllocation)
            .filter(
                ResourceAllocation.resource_account_id == account.id,
                ResourceAllocation.is_active.is_(True),
            )
            .count()
        )
        if (
            account.expires_at
            and account.status != ResourceStatus.DISABLED.value
            and 0 < (account.expires_at - today).days <= days
        ):
            if _create_if_absent(
                db,
                ntype=NotificationType.RESOURCE_EXPIRING.value,
                target_type="resource_account",
                target_id=str(account.id),
                period_key=period_key,
                title="资源即将到期",
                message=f"{account.resource_name} 将于 {account.expires_at.isoformat()} 到期",
                resource_account_id=account.id,
                due_date=account.expires_at,
            ):
                created += 1
        if (
            account.expires_at
            and account.expires_at <= today
            and account.status != ResourceStatus.DISABLED.value
        ):
            if _create_if_absent(
                db,
                ntype=NotificationType.RESOURCE_EXPIRED.value,
                target_type="resource_account",
                target_id=str(account.id),
                period_key=period_key,
                title="资源已到期",
                message=f"{account.resource_name} 已于 {account.expires_at.isoformat()} 到期",
                resource_account_id=account.id,
                due_date=account.expires_at,
            ):
                created += 1
        if account.status == ResourceStatus.ACTIVE.value and active_count == 0:
            if _create_if_absent(
                db,
                ntype=NotificationType.RESOURCE_UNASSIGNED.value,
                target_type="resource_account",
                target_id=str(account.id),
                period_key=period_key,
                title="资源未分配",
                message=f"{account.resource_name} 当前无有效分配",
                resource_account_id=account.id,
            ):
                created += 1

    due_rules = (
        db.query(RecurringExpenseRule)
        .filter(
            RecurringExpenseRule.is_active.is_(True),
            RecurringExpenseRule.next_run_date <= today,
        )
        .all()
    )
    for rule in due_rules:
        if _create_if_absent(
            db,
            ntype=NotificationType.RECURRING_RULE_DUE.value,
            target_type="recurring_expense_rule",
            target_id=str(rule.id),
            period_key=rule.next_run_date.isoformat(),
            title="周期规则待生成",
            message=f"{rule.name} 下次执行日 {rule.next_run_date.isoformat()}",
            resource_account_id=rule.resource_account_id,
            due_date=rule.next_run_date,
        ):
            created += 1

    db.commit()
    return created


def readable_notifications(db: Session, current_user: CurrentUser):
    query = db.query(Notification).options(
        joinedload(Notification.resource_account),
        joinedload(Notification.project),
    )
    if current_user.role in {"ADMIN", "BOSS"}:
        return query
    resource_ids = readable_resources(db, current_user).with_entities(ResourceAccount.id)
    return query.filter(Notification.resource_account_id.in_(resource_ids))


def list_notifications(
    db: Session,
    current_user: CurrentUser,
    *,
    status_filter: str | None,
    type_filter: str | None,
    page: int,
    page_size: int,
) -> NotificationListResponse:
    query = readable_notifications(db, current_user)
    if status_filter:
        query = query.filter(Notification.status == status_filter)
    if type_filter:
        query = query.filter(Notification.type == type_filter)
    total = query.order_by(None).count()
    items = (
        query.order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return NotificationListResponse(
        items=[_serialize(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def _get_readable(db: Session, current_user: CurrentUser, notification_id: int) -> Notification:
    item = readable_notifications(db, current_user).filter(Notification.id == notification_id).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提醒不存在")
    if item.resource_account_id and not can_read_resource(db, current_user, item.resource_account_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提醒不存在")
    return item


def mark_read(db: Session, current_user: CurrentUser, notification_id: int) -> NotificationPublic:
    item = _get_readable(db, current_user, notification_id)
    if item.status == NotificationStatus.UNREAD.value:
        item.status = NotificationStatus.READ.value
        item.read_at = _now()
        db.add(item)
        db.commit()
        db.refresh(item)
    return _serialize(item)


def mark_resolved(db: Session, current_user: CurrentUser, notification_id: int) -> NotificationPublic:
    item = _get_readable(db, current_user, notification_id)
    item.status = NotificationStatus.RESOLVED.value
    item.resolved_at = _now()
    if item.read_at is None:
        item.read_at = item.resolved_at
    db.add(item)
    db.commit()
    db.refresh(item)
    return _serialize(item)
