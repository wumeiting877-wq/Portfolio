from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.permissions.dependencies import CurrentUser, get_current_user
from app.services.settings_service import get_expiring_days
from app.schemas.statistics import (
    BillingCostResponse,
    EmployeeCostResponse,
    ExpiringResourceResponse,
    ExpenseTrendResponse,
    OverviewResponse,
    ProjectCostResponse,
    ResourceStatusResponse,
    ResourceTypeCostResponse,
)
from app.services.statistics_service import (
    get_billing_costs,
    get_employee_costs,
    get_expiring_resources,
    get_expense_trend,
    get_overview,
    get_project_costs,
    get_resource_status,
    get_resource_type_costs,
)

router = APIRouter(prefix="/api/statistics", tags=["statistics"])


@router.get("/overview", response_model=OverviewResponse, response_model_exclude_none=True)
def statistics_overview(
    date_from: date | None = None,
    date_to: date | None = None,
    project_id: int | None = None,
    employee_id: int | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OverviewResponse:
    return get_overview(
        db,
        current_user,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        employee_id=employee_id,
    )


@router.get("/expense-trend", response_model=ExpenseTrendResponse)
def statistics_expense_trend(
    date_from: date | None = None,
    date_to: date | None = None,
    project_id: int | None = None,
    employee_id: int | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExpenseTrendResponse:
    return get_expense_trend(
        db,
        current_user,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        employee_id=employee_id,
    )


@router.get("/project-costs", response_model=ProjectCostResponse)
def statistics_project_costs(
    date_from: date | None = None,
    date_to: date | None = None,
    project_id: int | None = None,
    limit: int = Query(default=5, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectCostResponse:
    return get_project_costs(
        db,
        current_user,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        limit=limit,
    )


@router.get("/employee-costs", response_model=EmployeeCostResponse)
def statistics_employee_costs(
    date_from: date | None = None,
    date_to: date | None = None,
    project_id: int | None = None,
    employee_id: int | None = None,
    limit: int = Query(default=5, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EmployeeCostResponse:
    return get_employee_costs(
        db,
        current_user,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        employee_id=employee_id,
        limit=limit,
    )


@router.get("/resource-type-costs", response_model=ResourceTypeCostResponse)
def statistics_resource_type_costs(
    date_from: date | None = None,
    date_to: date | None = None,
    project_id: int | None = None,
    employee_id: int | None = None,
    limit: int = Query(default=5, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResourceTypeCostResponse:
    return get_resource_type_costs(
        db,
        current_user,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        employee_id=employee_id,
        limit=limit,
    )


@router.get("/billing-costs", response_model=BillingCostResponse)
def statistics_billing_costs(
    date_from: date | None = None,
    date_to: date | None = None,
    project_id: int | None = None,
    employee_id: int | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BillingCostResponse:
    return get_billing_costs(
        db,
        current_user,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        employee_id=employee_id,
    )


@router.get("/resource-status", response_model=ResourceStatusResponse)
def statistics_resource_status(
    project_id: int | None = None,
    days: int | None = Query(default=None, ge=1, le=365),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResourceStatusResponse:
    return get_resource_status(
        db, current_user, project_id=project_id, days=days or get_expiring_days(db)
    )


@router.get("/expiring-resources", response_model=ExpiringResourceResponse)
def statistics_expiring_resources(
    days: int | None = Query(default=None, ge=1, le=365),
    project_id: int | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExpiringResourceResponse:
    return get_expiring_resources(
        db, current_user, days=days or get_expiring_days(db), project_id=project_id
    )
