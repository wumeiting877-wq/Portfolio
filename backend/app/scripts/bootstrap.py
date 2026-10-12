"""Bootstrap roles, system settings, and the initial admin.

Demo business accounts (boss / pm / member) stay on for development and test.
Production and pilot skip them unless BOOTSTRAP_DEMO_ACCOUNTS is explicitly true.
"""

import logging
import os

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging import configure_logging
from app.core.security import hash_password
from app.models.employee import Employee
from app.models.enums import EmploymentStatus, RoleCode, UserStatus
from app.models.role import Role
from app.models.user import User
from app.scripts.create_admin import create_admin

logger = logging.getLogger(__name__)

_TRUE_VALUES = {"1", "true", "yes", "on"}
_DEMO_ENVS = {"development", "dev", "test", "testing"}


def demo_accounts_enabled() -> bool:
    raw = os.getenv("BOOTSTRAP_DEMO_ACCOUNTS")
    if raw is not None and raw.strip() != "":
        return raw.strip().lower() in _TRUE_VALUES
    app_env = (os.getenv("APP_ENV") or settings.APP_ENV or "development").strip().lower()
    return app_env in _DEMO_ENVS


DEMO_ACCOUNTS = [
    {
        "username_env": "DEMO_BOSS_USERNAME",
        "password_env": "DEMO_BOSS_PASSWORD",
        "username_default": "boss",
        "employee_no": "BOSS001",
        "name": "老板",
        "role": RoleCode.BOSS.value,
    },
    {
        "username_env": "DEMO_PM_USERNAME",
        "password_env": "DEMO_PM_PASSWORD",
        "username_default": "pm",
        "employee_no": "PM001",
        "name": "项目负责人",
        "role": RoleCode.PROJECT_MANAGER.value,
    },
    {
        "username_env": "DEMO_MEMBER_USERNAME",
        "password_env": "DEMO_MEMBER_PASSWORD",
        "username_default": "member",
        "employee_no": "MB001",
        "name": "普通成员",
        "role": RoleCode.MEMBER.value,
    },
]


def _ensure_demo_user(db: Session, spec: dict[str, str]) -> None:
    username = os.getenv(spec["username_env"], spec["username_default"])
    password = os.getenv(spec["password_env"], "change_me")
    if db.query(User).filter(User.username == username).first():
        logger.info("Demo user already exists, skip: %s", username)
        return
    role = db.query(Role).filter(Role.code == spec["role"]).one()
    employee = db.query(Employee).filter(Employee.employee_no == spec["employee_no"]).first()
    if employee is None:
        employee = Employee(
            employee_no=spec["employee_no"],
            name=spec["name"],
            department="管理层" if spec["role"] != RoleCode.MEMBER.value else "业务部",
            position=spec["name"],
            employment_status=EmploymentStatus.ACTIVE.value,
        )
        db.add(employee)
        db.flush()
    db.add(
        User(
            username=username,
            password_hash=hash_password(password),
            employee_id=employee.id,
            role_id=role.id,
            status=UserStatus.ACTIVE.value,
            must_change_password=False,
        )
    )
    db.commit()
    logger.info("Demo user created: %s role=%s", username, spec["role"])


def main() -> None:
    configure_logging()
    db = SessionLocal()
    try:
        create_admin(db)
        from app.services.settings_service import get_or_create_settings

        get_or_create_settings(db)
        db.commit()
        if demo_accounts_enabled():
            for spec in DEMO_ACCOUNTS:
                _ensure_demo_user(db, spec)
        else:
            logger.info("Demo accounts skipped (BOOTSTRAP_DEMO_ACCOUNTS disabled for this environment)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
