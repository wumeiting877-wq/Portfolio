from sqlalchemy import false, or_
from sqlalchemy.orm import Query, Session

from app.models.enums import DataScope
from app.models.project import Project
from app.models.resource_account import ResourceAccount
from app.models.resource_allocation import ResourceAllocation
from app.permissions.dependencies import CurrentUser
from app.permissions.project_scope import readable_projects
from app.permissions.scopes import scope_for_role


def _scope_of(current_user: CurrentUser) -> DataScope:
    try:
        return DataScope(current_user.scope)
    except ValueError:
        return scope_for_role(current_user.role)


def _managed_or_member_project_ids(db: Session, current_user: CurrentUser) -> Query:
    return readable_projects(db, current_user).with_entities(Project.id)


def readable_resources(db: Session, current_user: CurrentUser) -> Query:
    """Backend-enforced resource visibility. Never return unscope'd rows."""
    query = db.query(ResourceAccount)
    scope = _scope_of(current_user)

    if scope == DataScope.GLOBAL:
        return query

    if current_user.employee_id is None:
        return query.filter(false())

    if scope == DataScope.MANAGED_PROJECTS:
        project_ids = _managed_or_member_project_ids(db, current_user)
        allocated = db.query(ResourceAllocation.resource_account_id).filter(
            ResourceAllocation.is_active.is_(True),
            ResourceAllocation.project_id.in_(project_ids),
        )
        return query.filter(ResourceAccount.id.in_(allocated))

    if scope == DataScope.MEMBER_PROJECTS:
        project_ids = _managed_or_member_project_ids(db, current_user)
        allocated = db.query(ResourceAllocation.resource_account_id).filter(
            ResourceAllocation.is_active.is_(True),
            ResourceAllocation.employee_id == current_user.employee_id,
            or_(
                ResourceAllocation.project_id.is_(None),
                ResourceAllocation.project_id.in_(project_ids),
            ),
        )
        return query.filter(ResourceAccount.id.in_(allocated))

    return query.filter(false())


def can_read_resource(db: Session, current_user: CurrentUser, resource_id: int) -> bool:
    return (
        readable_resources(db, current_user)
        .filter(ResourceAccount.id == resource_id)
        .first()
        is not None
    )


def readable_allocations(
    db: Session,
    current_user: CurrentUser,
    *,
    resource_id: int | None = None,
) -> Query:
    query = db.query(ResourceAllocation)
    if resource_id is not None:
        query = query.filter(ResourceAllocation.resource_account_id == resource_id)

    scope = _scope_of(current_user)
    if scope == DataScope.GLOBAL:
        return query

    if current_user.employee_id is None:
        return query.filter(false())

    if scope == DataScope.MANAGED_PROJECTS:
        project_ids = _managed_or_member_project_ids(db, current_user)
        return query.filter(ResourceAllocation.project_id.in_(project_ids))

    if scope == DataScope.MEMBER_PROJECTS:
        project_ids = _managed_or_member_project_ids(db, current_user)
        return query.filter(
            ResourceAllocation.employee_id == current_user.employee_id,
            or_(
                ResourceAllocation.project_id.is_(None),
                ResourceAllocation.project_id.in_(project_ids),
            ),
        )

    return query.filter(false())


def can_read_allocation(db: Session, current_user: CurrentUser, allocation_id: int) -> bool:
    return (
        readable_allocations(db, current_user)
        .filter(ResourceAllocation.id == allocation_id)
        .first()
        is not None
    )
