from sqlalchemy import false
from sqlalchemy.orm import Query, Session

from app.models.enums import DataScope
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.permissions.dependencies import CurrentUser
from app.permissions.scopes import scope_for_role


def _scope_of(current_user: CurrentUser) -> DataScope:
    try:
        return DataScope(current_user.scope)
    except ValueError:
        return scope_for_role(current_user.role)


def readable_projects(db: Session, current_user: CurrentUser) -> Query:
    """Backend-enforced project visibility. Never return unscope'd rows."""
    query = db.query(Project)
    scope = _scope_of(current_user)

    if scope == DataScope.GLOBAL:
        return query

    if scope == DataScope.MANAGED_PROJECTS:
        if current_user.employee_id is None:
            return query.filter(false())
        return query.filter(Project.manager_employee_id == current_user.employee_id)

    if scope == DataScope.MEMBER_PROJECTS:
        if current_user.employee_id is None:
            return query.filter(false())
        member_project_ids = (
            db.query(ProjectMember.project_id)
            .filter(
                ProjectMember.employee_id == current_user.employee_id,
                ProjectMember.is_active.is_(True),
            )
        )
        return query.filter(Project.id.in_(member_project_ids))

    return query.filter(false())


def can_read_project(db: Session, current_user: CurrentUser, project_id: int) -> bool:
    return (
        readable_projects(db, current_user).filter(Project.id == project_id).first() is not None
    )
