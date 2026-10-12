"""Create the initial administrator account from environment variables."""

import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging import configure_logging
from app.core.security import hash_password
from app.models.employee import Employee
from app.models.enums import EmploymentStatus, RoleCode, UserStatus
from app.models.role import Role
from app.models.user import User
from app.services.role_service import seed_roles

logger = logging.getLogger(__name__)


def create_admin(db: Session) -> None:
    seed_roles(db)
    existing = db.query(User).filter(User.username == settings.INITIAL_ADMIN_USERNAME).first()
    if existing:
        logger.info("Admin user already exists, skip creation")
        return

    admin_role = db.query(Role).filter(Role.code == RoleCode.ADMIN.value).one()
    employee = (
        db.query(Employee).filter(Employee.employee_no == "ADMIN001").first()
    )
    if employee is None:
        employee = Employee(
            employee_no="ADMIN001",
            name="系统管理员",
            department="管理部",
            position="管理员",
            employment_status=EmploymentStatus.ACTIVE.value,
        )
        db.add(employee)
        db.flush()

    db.add(
        User(
            username=settings.INITIAL_ADMIN_USERNAME,
            password_hash=hash_password(settings.INITIAL_ADMIN_PASSWORD),
            employee_id=employee.id,
            role_id=admin_role.id,
            status=UserStatus.ACTIVE.value,
            must_change_password=False,
        )
    )
    db.commit()
    logger.info("Admin user created: %s", settings.INITIAL_ADMIN_USERNAME)


def main() -> None:
    configure_logging()
    db = SessionLocal()
    try:
        create_admin(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
