from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.enterprise import AuditLogListResponse, AuditLogPublic
from app.services.audit_service import public_audit_payload


def _summary(before: dict | None, after: dict | None) -> str:
    if after and isinstance(after, dict):
        for key in ("name", "resource_name", "project_code", "employee_no", "action"):
            if after.get(key):
                return str(after[key])
        if after.get("import_type"):
            return f"导入 {after.get('import_type')} {after.get('created_count', '')}"
    if before and isinstance(before, dict):
        for key in ("name", "resource_name", "project_code"):
            if before.get(key):
                return str(before[key])
    return ""


def serialize_audit(log: AuditLog, username: str | None) -> AuditLogPublic:
    payload = public_audit_payload(log)
    return AuditLogPublic(
        id=payload["id"],
        operator_user_id=payload["operator_user_id"],
        operator_username=username,
        action=payload["action"],
        module=payload["module"],
        target_type=payload["target_type"],
        target_id=payload["target_id"],
        summary=_summary(payload.get("before_data"), payload.get("after_data")),
        before_data=payload.get("before_data"),
        after_data=payload.get("after_data"),
        ip_address=payload.get("ip_address"),
        created_at=payload["created_at"],
    )


def list_audit_logs(
    db: Session,
    *,
    operator: str | None,
    module: str | None,
    action: str | None,
    target_type: str | None,
    target_id: str | None,
    date_from: date | None,
    date_to: date | None,
    page: int,
    page_size: int,
) -> AuditLogListResponse:
    query = db.query(AuditLog)
    if operator:
        user_ids = db.query(User.id).filter(User.username.ilike(f"%{operator}%"))
        query = query.filter(AuditLog.operator_user_id.in_(user_ids))
    if module:
        query = query.filter(AuditLog.module == module)
    if action:
        query = query.filter(AuditLog.action == action)
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)
    if target_id:
        query = query.filter(AuditLog.target_id == str(target_id))
    if date_from is not None:
        start = datetime.combine(date_from, datetime.min.time())
        query = query.filter(AuditLog.created_at >= start)
    if date_to is not None:
        end = datetime.combine(date_to, datetime.max.time())
        query = query.filter(AuditLog.created_at <= end)
    total = query.order_by(None).count()
    items = (
        query.order_by(AuditLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    user_ids = {item.operator_user_id for item in items if item.operator_user_id}
    users = {
        user.id: user.username
        for user in db.query(User).filter(User.id.in_(user_ids)).all()
    } if user_ids else {}
    return AuditLogListResponse(
        items=[serialize_audit(item, users.get(item.operator_user_id or 0)) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_audit_log(db: Session, audit_id: int) -> AuditLogPublic:
    item = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="审计日志不存在")
    username = None
    if item.operator_user_id:
        user = db.query(User).filter(User.id == item.operator_user_id).first()
        username = user.username if user else None
    return serialize_audit(item, username)
