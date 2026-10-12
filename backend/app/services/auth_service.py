from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.enums import UserStatus
from app.models.user import User
from app.permissions.scopes import scope_for_role
from app.schemas.user import EmployeeBrief, UserPublic


LOGIN_FAILED_DETAIL = "用户名或密码错误"


def to_user_public(user: User) -> UserPublic:
    employee = None
    if user.employee is not None:
        employee = EmployeeBrief.model_validate(user.employee)
    return UserPublic(
        id=user.id,
        username=user.username,
        employee_id=user.employee_id,
        role_id=user.role_id,
        role_code=user.role.code,
        role_name=user.role.name,
        status=user.status,
        must_change_password=user.must_change_password,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        employee=employee,
    )


def authenticate_user(db: Session, username: str, password: str) -> User:
    user = (
        db.query(User)
        .options(joinedload(User.role), joinedload(User.employee))
        .filter(User.username == username)
        .first()
    )
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=LOGIN_FAILED_DETAIL)
    if user.status == UserStatus.DISABLED.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已停用")
    if user.status == UserStatus.LOCKED.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已锁定")
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def issue_token(user: User) -> str:
    return create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role.code,
        scope=scope_for_role(user.role.code).value,
    )


def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="原密码不正确")
    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    user.password_updated_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
