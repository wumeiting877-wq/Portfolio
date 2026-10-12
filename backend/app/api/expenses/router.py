from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.permissions.dependencies import CurrentUser, get_current_user, require_admin
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseListResponse,
    ExpensePublic,
    ExpenseUpdate,
    RecurringGenerateResult,
    SuggestedDistribution,
)
from app.services.expense_service import (
    create_expense,
    generate_recurring_expenses,
    get_readable_expense,
    list_expenses,
    serialize_expense,
    suggested_distributions,
    update_expense,
    void_expense,
)

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=ExpenseListResponse)
def get_expenses(
    keyword: str | None = None,
    expense_type_id: int | None = None,
    category: str | None = None,
    billing_mode: str | None = None,
    source: str | None = None,
    resource_account_id: int | None = None,
    project_id: int | None = None,
    employee_id: int | None = None,
    currency: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    billing_period: str | None = None,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExpenseListResponse:
    items, total, page, page_size = list_expenses(
        db,
        current_user,
        keyword=keyword,
        expense_type_id=expense_type_id,
        category=category,
        billing_mode=billing_mode,
        source=source,
        resource_account_id=resource_account_id,
        project_id=project_id,
        employee_id=employee_id,
        currency=currency,
        date_from=date_from,
        date_to=date_to,
        billing_period=billing_period,
        status_filter=status,
        page=page,
        page_size=page_size,
    )
    return ExpenseListResponse(
        items=[serialize_expense(db, current_user, item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/suggested-distributions", response_model=list[SuggestedDistribution])
def get_suggested_distributions(
    resource_account_id: int,
    amount: Decimal,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[SuggestedDistribution]:
    _ = current_user
    return suggested_distributions(db, resource_account_id, amount)


@router.post("/recurring/generate", response_model=RecurringGenerateResult)
def post_generate_recurring(
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RecurringGenerateResult:
    return generate_recurring_expenses(
        db,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )


@router.post("", response_model=ExpensePublic)
def post_expense(
    payload: ExpenseCreate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ExpensePublic:
    expense = create_expense(
        db,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_expense(db, current_user, expense)


@router.get("/{expense_id}", response_model=ExpensePublic)
def get_expense(
    expense_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExpensePublic:
    expense = get_readable_expense(db, current_user, expense_id)
    return serialize_expense(db, current_user, expense)


@router.put("/{expense_id}", response_model=ExpensePublic)
def put_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ExpensePublic:
    expense = update_expense(
        db,
        expense_id,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_expense(db, current_user, expense)


@router.post("/{expense_id}/void", response_model=ExpensePublic)
def post_void_expense(
    expense_id: int,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ExpensePublic:
    expense = void_expense(
        db,
        expense_id,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_expense(db, current_user, expense)
