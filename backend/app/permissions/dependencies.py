from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.enums import PermissionAction, RoleCode, UserStatus
from app.models.user import User
from app.permissions.roles import role_has_permission
from app.permissions.scopes import scope_for_role

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    id: int
    username: str
    role: str
    scope: str
    status: str
    must_change_password: bool
    employee_id: int | None
    user: User


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录") from None

    user_id = payload.get("user_id")
    user = (
        db.query(User)
        .options(joinedload(User.role), joinedload(User.employee))
        .filter(User.id == user_id)
        .first()
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    if user.status != UserStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

    role_code = user.role.code if user.role else str(payload.get("role") or "")
    return CurrentUser(
        id=user.id,
        username=user.username,
        role=role_code,
        scope=scope_for_role(role_code).value,
        status=user.status,
        must_change_password=user.must_change_password,
        employee_id=user.employee_id,
        user=user,
    )


def require_roles(*roles: RoleCode):
    allowed = {role.value for role in roles}

    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限")
        return current_user

    return dependency


def require_permission(action: PermissionAction):
    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not role_has_permission(current_user.role, action):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限")
        return current_user

    return dependency


require_admin = require_roles(RoleCode.ADMIN)
require_admin_or_boss = require_roles(RoleCode.ADMIN, RoleCode.BOSS)


def require_stable_identifier_admin(detail: str):
    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role != RoleCode.ADMIN.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
        return current_user

    return dependency
