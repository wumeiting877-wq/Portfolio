from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.permissions.dependencies import CurrentUser, get_current_user
from app.schemas.enterprise import NotificationListResponse, NotificationPublic
from app.services.notification_service import (
    generate_notifications,
    list_notifications,
    mark_read,
    mark_resolved,
)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
def get_notifications(
    status: str | None = None,
    type: str | None = Query(default=None, alias="type"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationListResponse:
    return list_notifications(
        db,
        current_user,
        status_filter=status,
        type_filter=type,
        page=page,
        page_size=page_size,
    )


@router.post("/refresh", response_model=NotificationListResponse)
def refresh_notifications(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationListResponse:
    generated = generate_notifications(db)
    result = list_notifications(
        db,
        current_user,
        status_filter=None,
        type_filter=None,
        page=1,
        page_size=20,
    )
    result.generated = generated
    return result


@router.post("/{notification_id}/read", response_model=NotificationPublic)
def read_notification(
    notification_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationPublic:
    return mark_read(db, current_user, notification_id)


@router.post("/{notification_id}/resolve", response_model=NotificationPublic)
def resolve_notification(
    notification_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationPublic:
    return mark_resolved(db, current_user, notification_id)
