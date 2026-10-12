from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.permissions.dependencies import (
    CurrentUser,
    get_current_user,
    require_admin,
    require_stable_identifier_admin,
)
from app.schemas.expense import ExpenseTypeCodeChange, ExpenseTypeCreate, ExpenseTypePublic, ExpenseTypeUpdate
from app.schemas.stable_identifier import IdentifierImpact
from app.services.expense_service import (
    correct_expense_type_code,
    create_expense_type,
    get_expense_type,
    list_expense_types,
    serialize_expense_type,
    set_expense_type_active,
    update_expense_type,
)
from app.services.stable_identifier_service import expense_type_identifier_impact

router = APIRouter(prefix="/api/expense-types", tags=["expense-types"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=list[ExpenseTypePublic])
def get_expense_types(
    include_inactive: bool = False,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ExpenseTypePublic]:
    return [
        serialize_expense_type(item)
        for item in list_expense_types(db, current_user, include_inactive=include_inactive)
    ]


@router.post("", response_model=ExpenseTypePublic)
def post_expense_type(
    payload: ExpenseTypeCreate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ExpenseTypePublic:
    expense_type = create_expense_type(
        db,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_expense_type(expense_type)


@router.get("/{type_id}", response_model=ExpenseTypePublic)
def get_expense_type_by_id(
    type_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExpenseTypePublic:
    _ = current_user
    return serialize_expense_type(get_expense_type(db, type_id))


@router.put("/{type_id}", response_model=ExpenseTypePublic)
def put_expense_type(
    type_id: int,
    payload: ExpenseTypeUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ExpenseTypePublic:
    expense_type = update_expense_type(
        db,
        type_id,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_expense_type(expense_type)


@router.get("/{type_id}/code/impact", response_model=IdentifierImpact)
def get_expense_type_code_impact(
    type_id: int,
    current_user: CurrentUser = Depends(require_stable_identifier_admin("无权限修正费用类型编码")),
    db: Session = Depends(get_db),
) -> IdentifierImpact:
    _ = current_user
    return expense_type_identifier_impact(db, type_id)


@router.patch("/{type_id}/code", response_model=ExpenseTypePublic)
def patch_expense_type_code(
    type_id: int,
    payload: ExpenseTypeCodeChange,
    request: Request,
    current_user: CurrentUser = Depends(require_stable_identifier_admin("无权限修正费用类型编码")),
    db: Session = Depends(get_db),
) -> ExpenseTypePublic:
    expense_type = correct_expense_type_code(
        db,
        type_id,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_expense_type(expense_type)


@router.post("/{type_id}/disable", response_model=ExpenseTypePublic)
def post_disable_expense_type(
    type_id: int,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ExpenseTypePublic:
    expense_type = set_expense_type_active(
        db,
        type_id,
        is_active=False,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_expense_type(expense_type)


@router.post("/{type_id}/enable", response_model=ExpenseTypePublic)
def post_enable_expense_type(
    type_id: int,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ExpenseTypePublic:
    expense_type = set_expense_type_active(
        db,
        type_id,
        is_active=True,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_expense_type(expense_type)
