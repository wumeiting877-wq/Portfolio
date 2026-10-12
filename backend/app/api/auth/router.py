from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.permissions.dependencies import CurrentUser, get_current_user
from app.permissions.scopes import scope_for_role
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LoginResponse, MeResponse
from app.services.auth_service import authenticate_user, change_password, issue_token, to_user_public

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = authenticate_user(db, payload.username, payload.password)
    return LoginResponse(
        access_token=issue_token(user),
        must_change_password=user.must_change_password,
        user=to_user_public(user),
    )


@router.get("/me", response_model=MeResponse)
def me(current_user: CurrentUser = Depends(get_current_user)) -> MeResponse:
    employee_name = current_user.user.employee.name if current_user.user.employee else None
    return MeResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        role_name=current_user.user.role.name,
        scope=scope_for_role(current_user.role).value,
        status=current_user.status,
        must_change_password=current_user.must_change_password,
        employee_id=current_user.employee_id,
        employee_name=employee_name,
    )


@router.post("/change-password")
def change_current_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    change_password(db, current_user.user, payload.old_password, payload.new_password)
    return {"status": "ok"}


@router.post("/logout")
def logout() -> dict[str, str]:
    return {"status": "ok"}
