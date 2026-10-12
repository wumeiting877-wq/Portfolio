from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.permissions.dependencies import CurrentUser, require_admin, require_admin_or_boss
from app.schemas.settings import SystemSettingsPublic, SystemSettingsUpdate
from app.services.settings_service import get_settings_public, serialize_settings, update_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=SystemSettingsPublic)
def get_settings(
    current_user: CurrentUser = Depends(require_admin_or_boss),
    db: Session = Depends(get_db),
) -> SystemSettingsPublic:
    return get_settings_public(db)


@router.put("", response_model=SystemSettingsPublic)
def put_settings(
    payload: SystemSettingsUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> SystemSettingsPublic:
    row = update_settings(
        db,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_settings(row)
