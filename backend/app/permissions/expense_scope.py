from sqlalchemy import false
from sqlalchemy.orm import Query, Session

from app.models.enums import DataScope
from app.models.expense_distribution import ExpenseDistribution
from app.models.expense_record import ExpenseRecord
from app.models.project import Project
from app.permissions.dependencies import CurrentUser
from app.permissions.project_scope import readable_projects
from app.permissions.scopes import scope_for_role


def _scope_of(current_user: CurrentUser) -> DataScope:
    try:
        return DataScope(current_user.scope)
    except ValueError:
        return scope_for_role(current_user.role)


def _managed_project_ids(db: Session, current_user: CurrentUser) -> Query:
    return readable_projects(db, current_user).with_entities(Project.id)


def readable_expenses(db: Session, current_user: CurrentUser) -> Query:
    """Backend-enforced expense visibility. Never return unscope'd rows."""
    query = db.query(ExpenseRecord)
    scope = _scope_of(current_user)

    if scope == DataScope.GLOBAL:
        return query

    if current_user.employee_id is None:
        return query.filter(false())

    if scope == DataScope.MANAGED_PROJECTS:
        project_ids = _managed_project_ids(db, current_user)
        matched = db.query(ExpenseDistribution.expense_record_id).filter(
            ExpenseDistribution.project_id.in_(project_ids)
        )
        return query.filter(ExpenseRecord.id.in_(matched))

    if scope == DataScope.MEMBER_PROJECTS:
        matched = db.query(ExpenseDistribution.expense_record_id).filter(
            ExpenseDistribution.employee_id == current_user.employee_id
        )
        return query.filter(ExpenseRecord.id.in_(matched))

    return query.filter(false())


def can_read_expense(db: Session, current_user: CurrentUser, expense_id: int) -> bool:
    return (
        readable_expenses(db, current_user).filter(ExpenseRecord.id == expense_id).first() is not None
    )


def readable_distributions(
    db: Session,
    current_user: CurrentUser,
    *,
    expense_id: int | None = None,
) -> Query:
    query = db.query(ExpenseDistribution)
    if expense_id is not None:
        query = query.filter(ExpenseDistribution.expense_record_id == expense_id)

    scope = _scope_of(current_user)
    if scope == DataScope.GLOBAL:
        return query

    if current_user.employee_id is None:
        return query.filter(false())

    if scope == DataScope.MANAGED_PROJECTS:
        project_ids = _managed_project_ids(db, current_user)
        return query.filter(ExpenseDistribution.project_id.in_(project_ids))

    if scope == DataScope.MEMBER_PROJECTS:
        return query.filter(ExpenseDistribution.employee_id == current_user.employee_id)

    return query.filter(false())


def can_read_distribution(db: Session, current_user: CurrentUser, distribution_id: int) -> bool:
    return (
        readable_distributions(db, current_user)
        .filter(ExpenseDistribution.id == distribution_id)
        .first()
        is not None
    )


def is_global_expense_reader(current_user: CurrentUser) -> bool:
    return _scope_of(current_user) == DataScope.GLOBAL
