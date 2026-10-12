from sqlalchemy.orm import Session

from app.models.enums import RoleCode
from app.models.role import Role

DEFAULT_ROLES = [
    (RoleCode.ADMIN.value, "系统管理员", "全局读写"),
    (RoleCode.BOSS.value, "老板", "全局只读"),
    (RoleCode.PROJECT_MANAGER.value, "项目负责人", "负责项目只读"),
    (RoleCode.MEMBER.value, "普通成员", "参与项目只读"),
]


def seed_roles(db: Session) -> None:
    existing = {role.code for role in db.query(Role).all()}
    for code, name, description in DEFAULT_ROLES:
        if code not in existing:
            db.add(Role(code=code, name=name, description=description))
    db.flush()
