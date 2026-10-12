from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import hash_password
from app.models.employee import Employee
from app.models.enums import UserStatus
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UsernameChange
from app.services.audit_service import write_audit
from app.services.stable_identifier_service import (
    commit_stable_identifier,
    normalize_stable_identifier,
    reject_same,
    reject_taken,
)
from app.services.auth_service import to_user_public


def get_user(db: Session, user_id: int) -> User:
    user = (
        db.query(User)
        .options(joinedload(User.role), joinedload(User.employee))
        .filter(User.id == user_id)
        .first()
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账号不存在")
    return user


def _snapshot(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "employee_id": user.employee_id,
        "role_id": user.role_id,
        "status": user.status,
        "must_change_password": user.must_change_password,
    }


def list_users(db: Session) -> list[User]:
    return (
        db.query(User)
        .options(joinedload(User.role), joinedload(User.employee))
        .order_by(User.id.asc())
        .all()
    )


def create_user(
    db: Session,
    payload: UserCreate,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> User:
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    role = db.query(Role).filter(Role.id == payload.role_id).first()
    if role is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色不存在")
    if payload.employee_id is not None:
        employee = db.query(Employee).filter(Employee.id == payload.employee_id).first()
        if employee is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="人员不存在")
        if db.query(User).filter(User.employee_id == payload.employee_id).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该人员已绑定账号")
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        employee_id=payload.employee_id,
        role_id=payload.role_id,
        status=UserStatus.ACTIVE.value,
        must_change_password=True,
        password_updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.flush()
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="create_user",
        module="users",
        target_type="user",
        target_id=user.id,
        after_data=_snapshot(user),
        ip_address=ip_address,
    )
    db.commit()
    return get_user(db, user.id)


def update_user(
    db: Session,
    user_id: int,
    payload: UserUpdate,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> User:
    user = get_user(db, user_id)
    before = _snapshot(user)
    data = payload.model_dump(exclude_unset=True)
    data.pop("username", None)
    data.pop("password", None)
    data.pop("password_hash", None)
    action = "update_user"
    if "role_id" in data and data["role_id"] is not None:
        role = db.query(Role).filter(Role.id == data["role_id"]).first()
        if role is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色不存在")
        action = "update_user_role"
    if "employee_id" in data and data["employee_id"] is not None:
        employee = db.query(Employee).filter(Employee.id == data["employee_id"]).first()
        if employee is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="人员不存在")
        bound = (
            db.query(User)
            .filter(User.employee_id == data["employee_id"], User.id != user_id)
            .first()
        )
        if bound:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该人员已绑定账号")
    if "status" in data and data["status"] is not None:
        try:
            UserStatus(data["status"])
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="无效的账号状态"
            ) from exc
    for key, value in data.items():
        setattr(user, key, value)
    db.add(user)
    db.flush()
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action=action,
        module="users",
        target_type="user",
        target_id=user.id,
        before_data=before,
        after_data=_snapshot(user),
        ip_address=ip_address,
    )
    db.commit()
    return get_user(db, user.id)


def correct_username(
    db: Session,
    user_id: int,
    payload: UsernameChange,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> User:
    user = get_user(db, user_id)
    new_value = normalize_stable_identifier(
        payload.new_username,
        max_length=80,
        invalid_detail="用户名格式不合法",
    )
    reject_same(new_value, user.username, "新用户名与当前用户名一致")
    taken = db.query(User).filter(User.username == new_value).first()
    reject_taken(taken.id if taken else None, user.id, "用户名已存在")
    previous = user.username
    user.username = new_value
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="USERNAME_CHANGE",
        module="users",
        target_type="user",
        target_id=user.id,
        before_data={"username": previous},
        after_data={"username": new_value},
        ip_address=ip_address,
    )
    commit_stable_identifier(
        db,
        constraint_names=("ix_users_username", "users_username_key"),
        duplicate_detail="用户名已存在",
        failure_detail="用户名修正失败",
    )
    return get_user(db, user.id)


def reset_password(
    db: Session,
    user_id: int,
    password: str,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> User:
    user = get_user(db, user_id)
    before = _snapshot(user)
    user.password_hash = hash_password(password)
    user.must_change_password = True
    user.password_updated_at = datetime.now(timezone.utc)
    db.add(user)
    db.flush()
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="reset_password",
        module="users",
        target_type="user",
        target_id=user.id,
        before_data=before,
        after_data=_snapshot(user),
        ip_address=ip_address,
    )
    db.commit()
    return get_user(db, user.id)


def set_user_status(
    db: Session,
    user_id: int,
    status_value: UserStatus,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> User:
    user = get_user(db, user_id)
    before = _snapshot(user)
    user.status = status_value.value
    db.add(user)
    db.flush()
    action = "enable_user" if status_value == UserStatus.ACTIVE else "disable_user"
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action=action,
        module="users",
        target_type="user",
        target_id=user.id,
        before_data=before,
        after_data=_snapshot(user),
        ip_address=ip_address,
    )
    db.commit()
    return get_user(db, user.id)


def serialize_user(user: User):
    return to_user_public(user)
