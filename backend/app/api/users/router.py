from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.enums import UserStatus
from app.permissions.dependencies import CurrentUser, require_admin, require_stable_identifier_admin
from app.schemas.stable_identifier import IdentifierImpact
from app.schemas.user import PasswordReset, UserCreate, UserPublic, UserUpdate, UsernameChange
from app.services.stable_identifier_service import username_identifier_impact
from app.services.user_service import (
    correct_username,
    create_user,
    get_user,
    list_users,
    reset_password,
    serialize_user,
    set_user_status,
    update_user,
)

router = APIRouter(prefix="/api/users", tags=["users"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=list[UserPublic])
def get_users(
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[UserPublic]:
    _ = current_user
    return [serialize_user(user) for user in list_users(db)]


@router.post("", response_model=UserPublic)
def post_user(
    payload: UserCreate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserPublic:
    user = create_user(
        db,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_user(user)


@router.get("/{user_id}", response_model=UserPublic)
def get_user_by_id(
    user_id: int,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserPublic:
    _ = current_user
    return serialize_user(get_user(db, user_id))


@router.put("/{user_id}", response_model=UserPublic)
def put_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserPublic:
    user = update_user(
        db,
        user_id,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_user(user)


@router.get("/{user_id}/username/impact", response_model=IdentifierImpact)
def get_username_impact(
    user_id: int,
    current_user: CurrentUser = Depends(require_stable_identifier_admin("无权限修正用户名")),
    db: Session = Depends(get_db),
) -> IdentifierImpact:
    _ = current_user
    return username_identifier_impact(db, user_id)


@router.patch("/{user_id}/username", response_model=UserPublic)
def patch_username(
    user_id: int,
    payload: UsernameChange,
    request: Request,
    current_user: CurrentUser = Depends(require_stable_identifier_admin("无权限修正用户名")),
    db: Session = Depends(get_db),
) -> UserPublic:
    user = correct_username(
        db,
        user_id,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_user(user)


@router.post("/{user_id}/reset-password", response_model=UserPublic)
def post_reset_password(
    user_id: int,
    payload: PasswordReset,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserPublic:
    user = reset_password(
        db,
        user_id,
        payload.password,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_user(user)


@router.post("/{user_id}/disable", response_model=UserPublic)
def post_disable_user(
    user_id: int,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserPublic:
    user = set_user_status(
        db,
        user_id,
        UserStatus.DISABLED,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_user(user)


@router.post("/{user_id}/enable", response_model=UserPublic)
def post_enable_user(
    user_id: int,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserPublic:
    user = set_user_status(
        db,
        user_id,
        UserStatus.ACTIVE,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_user(user)
