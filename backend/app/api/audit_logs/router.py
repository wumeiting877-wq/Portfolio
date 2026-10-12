from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.permissions.dependencies import CurrentUser, require_admin_or_boss
from app.schemas.enterprise import AuditLogListResponse, AuditLogPublic
from app.services.audit_query_service import get_audit_log, list_audit_logs

router = APIRouter(prefix="/api/audit-logs", tags=["audit-logs"])


@router.get("", response_model=AuditLogListResponse)
def get_audit_logs(
    operator: str | None = None,
    module: str | None = None,
    action: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_admin_or_boss),
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    return list_audit_logs(
        db,
        operator=operator,
        module=module,
        action=action,
        target_type=target_type,
        target_id=target_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )


@router.get("/{audit_id}", response_model=AuditLogPublic)
def get_audit_log_detail(
    audit_id: int,
    current_user: CurrentUser = Depends(require_admin_or_boss),
    db: Session = Depends(get_db),
) -> AuditLogPublic:
    return get_audit_log(db, audit_id)
