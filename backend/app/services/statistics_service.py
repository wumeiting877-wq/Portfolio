from datetime import date

from fastapi import HTTPException, status

from sqlalchemy.orm import Session

from app.models.enums import RoleCode
from app.models.resource_account import ResourceAccount
from app.permissions.dependencies import CurrentUser
from app.repositories.resource_repository import EXPIRING_SOON_DAYS
from app.repositories.statistics_repository import StatisticsRepository
from app.services.settings_service import business_today, get_expiring_days
from app.schemas.statistics import (
    BillingCostItem,
    BillingCostResponse,
    EmployeeCostItem,
    EmployeeCostResponse,
    ExpiringResourceResponse,
    ExpenseTrendResponse,
    OverviewResponse,
    ProjectCostItem,
    ProjectCostResponse,
    ProjectPublicCostItem,
    ResourceStatusBrief,
    ResourceStatusResponse,
    ResourceTypeCostItem,
    ResourceTypeCostResponse,
    TrendPoint,
)


def _is_member(current_user: CurrentUser) -> bool:
    return current_user.role == RoleCode.MEMBER.value


def _deny_member_ranking(current_user: CurrentUser) -> None:
    if _is_member(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限")


def _days_remaining(expires_at: date | None, today: date) -> int | None:
    if expires_at is None:
        return None
    return (expires_at - today).days


def _resource_brief(account: ResourceAccount, today: date) -> ResourceStatusBrief:
    type_name = account.resource_type.name if account.resource_type else None
    return ResourceStatusBrief(
        id=account.id,
        resource_name=account.resource_name,
        status=account.status,
        expires_at=account.expires_at,
        resource_type_name=type_name,
        days_remaining=_days_remaining(account.expires_at, today),
    )


def get_overview(
    db: Session,
    current_user: CurrentUser,
    *,
    date_from: date | None,
    date_to: date | None,
    project_id: int | None = None,
    employee_id: int | None = None,
    days: int | None = None,
) -> OverviewResponse:
    days = days or get_expiring_days(db)
    repo = StatisticsRepository(db)
    amounts = repo.amounts_by_currency(
        current_user,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        employee_id=employee_id,
    )
    if _is_member(current_user):
        counts = repo.resource_status_counts(
            current_user, project_id=project_id, days=days, today=business_today(db)
        )
        return OverviewResponse(
            amounts_by_currency=amounts,
            my_project_count=repo.project_count(current_user, project_id=project_id),
            my_resource_count=counts["total"],
            my_expiring_resource_count=counts["EXPIRING_SOON"],
        )
    counts = repo.resource_status_counts(
        current_user, project_id=project_id, days=days, today=business_today(db)
    )
    return OverviewResponse(
        amounts_by_currency=amounts,
        project_count=repo.project_count(current_user, project_id=project_id),
        employee_count=repo.employee_count(current_user, project_id=project_id),
        resource_count=counts["total"],
        active_resource_count=counts["ACTIVE"],
        idle_resource_count=counts["IDLE"],
        unassigned_active_resource_count=counts["UNASSIGNED_ACTIVE"],
        expired_resource_count=counts["EXPIRED"],
        expiring_soon_count=counts["EXPIRING_SOON"],
    )


def get_expense_trend(
    db: Session,
    current_user: CurrentUser,
    *,
    date_from: date | None,
    date_to: date | None,
    project_id: int | None = None,
    employee_id: int | None = None,
) -> ExpenseTrendResponse:
    repo = StatisticsRepository(db)
    rows = repo.expense_trend(
        current_user,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        employee_id=employee_id,
    )
    return ExpenseTrendResponse(
        series=[TrendPoint(period=period, currency=currency, amount=amount) for period, currency, amount in rows]
    )


def get_project_costs(
    db: Session,
    current_user: CurrentUser,
    *,
    date_from: date | None,
    date_to: date | None,
    project_id: int | None = None,
    limit: int,
) -> ProjectCostResponse:
    _deny_member_ranking(current_user)
    repo = StatisticsRepository(db)
    rows = repo.project_costs(
        current_user,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        limit=limit,
    )
    return ProjectCostResponse(
        items=[
            ProjectCostItem(
                project_id=project_id_,
                project_name=project_name,
                currency=currency,
                allocated_amount=amount,
            )
            for project_id_, project_name, currency, amount in rows
        ]
    )


def get_employee_costs(
    db: Session,
    current_user: CurrentUser,
    *,
    date_from: date | None,
    date_to: date | None,
    project_id: int | None = None,
    employee_id: int | None = None,
    limit: int,
) -> EmployeeCostResponse:
    _deny_member_ranking(current_user)
    repo = StatisticsRepository(db)
    rows = repo.employee_costs(
        current_user,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        employee_id=employee_id,
        limit=limit,
    )
    public_rows = repo.project_public_costs(
        current_user,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        limit=limit,
    )
    return EmployeeCostResponse(
        items=[
            EmployeeCostItem(
                employee_id=emp_id,
                employee_name=name,
                employee_no=employee_no,
                currency=currency,
                allocated_amount=amount,
            )
            for emp_id, name, employee_no, currency, amount in rows
        ],
        project_public_costs=[
            ProjectPublicCostItem(
                project_id=proj_id,
                project_name=name,
                currency=currency,
                allocated_amount=amount,
            )
            for proj_id, name, currency, amount in public_rows
        ],
    )


def get_resource_type_costs(
    db: Session,
    current_user: CurrentUser,
    *,
    date_from: date | None,
    date_to: date | None,
    project_id: int | None = None,
    employee_id: int | None = None,
    limit: int,
) -> ResourceTypeCostResponse:
    repo = StatisticsRepository(db)
    rows = repo.resource_type_costs(
        current_user,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        employee_id=employee_id,
        limit=limit,
    )
    return ResourceTypeCostResponse(
        items=[
            ResourceTypeCostItem(
                resource_type_id=type_id,
                resource_type_code=code,
                resource_type_name=name,
                currency=currency,
                allocated_amount=amount,
            )
            for type_id, code, name, currency, amount in rows
        ]
    )


def get_billing_costs(
    db: Session,
    current_user: CurrentUser,
    *,
    date_from: date | None,
    date_to: date | None,
    project_id: int | None = None,
    employee_id: int | None = None,
) -> BillingCostResponse:
    repo = StatisticsRepository(db)
    rows = repo.billing_costs(
        current_user,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        employee_id=employee_id,
    )
    return BillingCostResponse(
        items=[
            BillingCostItem(
                billing_mode=billing_mode,
                category=category,
                currency=currency,
                allocated_amount=amount,
            )
            for billing_mode, category, currency, amount in rows
        ]
    )


def get_resource_status(
    db: Session,
    current_user: CurrentUser,
    *,
    project_id: int | None = None,
    days: int | None = None,
) -> ResourceStatusResponse:
    days = days or get_expiring_days(db)
    repo = StatisticsRepository(db)
    today = business_today(db)
    counts = repo.resource_status_counts(current_user, project_id=project_id, days=days, today=today)
    public_counts = {
        "ACTIVE": counts["ACTIVE"],
        "IDLE": counts["IDLE"],
        "EXPIRED": counts["EXPIRED"],
        "DISABLED": counts["DISABLED"],
        "EXPIRING_SOON": counts["EXPIRING_SOON"],
        "UNASSIGNED_ACTIVE": counts["UNASSIGNED_ACTIVE"],
    }
    return ResourceStatusResponse(
        counts=public_counts,
        explicit_idle_count=counts["IDLE"],
        unassigned_active_count=counts["UNASSIGNED_ACTIVE"],
        idle_resources=[_resource_brief(item, today) for item in repo.idle_resources(current_user, project_id=project_id)],
        unassigned_active_resources=[
            _resource_brief(item, today)
            for item in repo.unassigned_active_resources(current_user, project_id=project_id)
        ],
    )


def get_expiring_resources(
    db: Session,
    current_user: CurrentUser,
    *,
    days: int,
    project_id: int | None = None,
) -> ExpiringResourceResponse:
    repo = StatisticsRepository(db)
    today = business_today(db)
    items = repo.expiring_resources(current_user, days=days, project_id=project_id, today=today)
    return ExpiringResourceResponse(
        days=days,
        items=[_resource_brief(item, today) for item in items],
    )
