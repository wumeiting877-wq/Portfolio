from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.permissions.dependencies import CurrentUser, require_admin, require_admin_or_boss
from app.schemas.expense import RecurringRuleCreate, RecurringRulePublic, RecurringRuleUpdate
from app.services.expense_service import (
    create_recurring_rule,
    get_recurring_rule,
    list_recurring_rules,
    serialize_rule,
    set_recurring_rule_active,
    update_recurring_rule,
)

router = APIRouter(prefix="/api/recurring-expense-rules", tags=["recurring-expense-rules"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=list[RecurringRulePublic])
def get_recurring_rules(
    include_inactive: bool = False,
    current_user: CurrentUser = Depends(require_admin_or_boss),
    db: Session = Depends(get_db),
) -> list[RecurringRulePublic]:
    show_inactive = include_inactive and current_user.role == "ADMIN"
    return [serialize_rule(item) for item in list_recurring_rules(db, include_inactive=show_inactive)]


@router.post("", response_model=RecurringRulePublic)
def post_recurring_rule(
    payload: RecurringRuleCreate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RecurringRulePublic:
    rule = create_recurring_rule(
        db,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_rule(rule)


@router.get("/{rule_id}", response_model=RecurringRulePublic)
def get_recurring_rule_by_id(
    rule_id: int,
    current_user: CurrentUser = Depends(require_admin_or_boss),
    db: Session = Depends(get_db),
) -> RecurringRulePublic:
    _ = current_user
    return serialize_rule(get_recurring_rule(db, rule_id))


@router.put("/{rule_id}", response_model=RecurringRulePublic)
def put_recurring_rule(
    rule_id: int,
    payload: RecurringRuleUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RecurringRulePublic:
    rule = update_recurring_rule(
        db,
        rule_id,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_rule(rule)


@router.post("/{rule_id}/disable", response_model=RecurringRulePublic)
def post_disable_recurring_rule(
    rule_id: int,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RecurringRulePublic:
    rule = set_recurring_rule_active(
        db,
        rule_id,
        is_active=False,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_rule(rule)


@router.post("/{rule_id}/enable", response_model=RecurringRulePublic)
def post_enable_recurring_rule(
    rule_id: int,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RecurringRulePublic:
    rule = set_recurring_rule_active(
        db,
        rule_id,
        is_active=True,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_rule(rule)
