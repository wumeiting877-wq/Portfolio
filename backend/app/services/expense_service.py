from calendar import monthrange
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.money import (
    amounts_equal,
    quantize_amount,
    quantize_money,
    quantize_ratio,
    split_by_ratio,
    split_equal,
    to_decimal,
)
from app.models.enums import (
    AllocationMethod,
    BillingMode,
    CurrencyCode,
    ExpenseCategory,
    ExpenseSource,
    ExpenseStatus,
    RecurringFrequency,
)
from app.models.expense_distribution import ExpenseDistribution
from app.models.expense_record import ExpenseRecord
from app.models.expense_type import ExpenseType
from app.models.recurring_expense_rule import RecurringExpenseRule
from app.models.recurring_rule_distribution import RecurringRuleDistribution
from app.models.resource_allocation import ResourceAllocation
from app.permissions.dependencies import CurrentUser
from app.permissions.expense_scope import (
    can_read_expense,
    is_global_expense_reader,
    readable_distributions,
    readable_expenses,
)
from app.repositories.expense_repository import ExpenseRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.resource_repository import ResourceRepository
from app.schemas.expense import (
    ExpenseTypeCodeChange,
    ExpenseCreate,
    ExpenseDistributionInput,
    ExpenseDistributionPublic,
    ExpensePublic,
    ExpenseTypeBrief,
    ExpenseTypeCreate,
    ExpenseTypePublic,
    ExpenseTypeUpdate,
    ExpenseUpdate,
    RecurringGenerateResult,
    RecurringRuleCreate,
    RecurringRuleDistributionInput,
    RecurringRuleDistributionPublic,
    RecurringRulePublic,
    RecurringRuleUpdate,
    SuggestedDistribution,
)
from app.services.audit_service import write_audit
from app.services.employee_service import get_employee
from app.services.stable_identifier_service import (
    commit_stable_identifier,
    normalize_stable_identifier,
    reject_same,
    reject_taken,
)
from app.services.settings_service import business_today


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_enum(value: str, enum_cls, detail: str) -> str:
    try:
        return enum_cls(value).value
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from exc


def _validate_currency(value: str) -> str:
    return _validate_enum(value, CurrencyCode, "无效的币种")


def _require_project_member(db: Session, project_id: int, employee_id: int) -> None:
    member = ProjectRepository(db).get_member(project_id, employee_id)
    if member is None or not member.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该成员不属于此项目")


def _validate_targets(db: Session, project_id: int | None, employee_id: int | None) -> None:
    if project_id is None and employee_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="项目与成员至少选择一项")
    if project_id is not None:
        project = ProjectRepository(db).get_by_id(project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    if employee_id is not None:
        get_employee(db, employee_id)
    if project_id is not None and employee_id is not None:
        _require_project_member(db, project_id, employee_id)


def _require_positive_amount(value: Decimal) -> Decimal:
    amount = quantize_amount(value)
    if amount < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="金额不能为负数")
    return amount


def resolve_distribution_amounts(
    total: Decimal,
    items: list[ExpenseDistributionInput] | list[RecurringRuleDistributionInput],
) -> list[tuple[ExpenseDistributionInput | RecurringRuleDistributionInput, Decimal, Decimal | None]]:
    if not items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="至少需要一条费用归属")
    total = _require_positive_amount(total)
    methods = {item.allocation_method for item in items}
    resolved: list[tuple[ExpenseDistributionInput | RecurringRuleDistributionInput, Decimal, Decimal | None]] = []

    if methods == {AllocationMethod.EQUAL.value} and all(item.allocated_amount is None for item in items):
        amounts = split_equal(total, len(items))
        for item, amount in zip(items, amounts, strict=True):
            resolved.append((item, amount, None))
    elif methods == {AllocationMethod.RATIO.value} and all(item.allocated_amount is None for item in items):
        if any(item.allocation_ratio is None for item in items):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="按比例分摊必须提供比例")
        ratios = [quantize_ratio(item.allocation_ratio) for item in items]
        amounts = split_by_ratio(total, ratios)
        for item, amount, ratio in zip(items, amounts, ratios, strict=True):
            resolved.append((item, amount, ratio))
    else:
        for item in items:
            if item.allocated_amount is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分摊金额不能为空")
            ratio = quantize_ratio(item.allocation_ratio) if item.allocation_ratio is not None else None
            resolved.append((item, _require_positive_amount(item.allocated_amount), ratio))

    allocated_sum = sum((row[1] for row in resolved), Decimal("0"))
    if not amounts_equal(allocated_sum, total):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="分摊金额合计必须等于费用金额",
        )
    return resolved


def validate_and_build_distributions(
    db: Session,
    total: Decimal,
    items: list[ExpenseDistributionInput],
) -> list[ExpenseDistribution]:
    resolved = resolve_distribution_amounts(total, items)
    distributions: list[ExpenseDistribution] = []
    for item, amount, ratio in resolved:
        method = _validate_enum(item.allocation_method, AllocationMethod, "无效的分摊方式")
        _validate_targets(db, item.project_id, item.employee_id)
        distributions.append(
            ExpenseDistribution(
                project_id=item.project_id,
                employee_id=item.employee_id,
                allocation_method=method,
                allocation_ratio=ratio,
                allocated_amount=amount,
            )
        )
    return distributions


def _validate_rule_templates(
    db: Session,
    total: Decimal,
    items: list[RecurringRuleDistributionInput],
) -> list[RecurringRuleDistribution]:
    resolved = resolve_distribution_amounts(total, items)
    rows: list[RecurringRuleDistribution] = []
    for item, amount, ratio in resolved:
        method = _validate_enum(item.allocation_method, AllocationMethod, "无效的分摊方式")
        _validate_targets(db, item.project_id, item.employee_id)
        rows.append(
            RecurringRuleDistribution(
                project_id=item.project_id,
                employee_id=item.employee_id,
                allocation_method=method,
                allocation_ratio=ratio,
                allocated_amount=amount,
            )
        )
    return rows


def serialize_expense_type(expense_type: ExpenseType) -> ExpenseTypePublic:
    return ExpenseTypePublic.model_validate(expense_type)


def _type_brief(expense_type: ExpenseType) -> ExpenseTypeBrief:
    return ExpenseTypeBrief(
        id=expense_type.id,
        code=expense_type.code,
        name=expense_type.name,
        category=expense_type.category,
    )


def serialize_distribution(item: ExpenseDistribution) -> ExpenseDistributionPublic:
    project = item.project
    employee = item.employee
    return ExpenseDistributionPublic(
        id=item.id,
        expense_record_id=item.expense_record_id,
        project_id=item.project_id,
        project_name=project.name if project else None,
        project_code=project.project_code if project else None,
        employee_id=item.employee_id,
        employee_name=employee.name if employee else None,
        employee_no=employee.employee_no if employee else None,
        allocation_method=item.allocation_method,
        allocation_ratio=item.allocation_ratio,
        allocated_amount=item.allocated_amount,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _attribution_text(items: list[ExpenseDistribution]) -> str:
    labels: list[str] = []
    for item in items:
        parts: list[str] = []
        if item.project is not None:
            parts.append(item.project.name)
        if item.employee is not None:
            parts.append(item.employee.name)
        labels.append(" / ".join(parts) if parts else "-")
    return "；".join(labels) if labels else "-"


def serialize_expense(
    db: Session,
    current_user: CurrentUser,
    expense: ExpenseRecord,
) -> ExpensePublic:
    visible = (
        readable_distributions(db, current_user, expense_id=expense.id)
        .options(
            joinedload(ExpenseDistribution.project),
            joinedload(ExpenseDistribution.employee),
        )
        .order_by(ExpenseDistribution.id.asc())
        .all()
    )
    visible_amount = sum((item.allocated_amount for item in visible), Decimal("0"))
    global_reader = is_global_expense_reader(current_user)
    amount = expense.amount if global_reader else visible_amount
    resource = expense.resource_account
    return ExpensePublic(
        id=expense.id,
        expense_type=_type_brief(expense.expense_type),
        resource_account_id=expense.resource_account_id,
        resource_name=resource.resource_name if resource else None,
        billing_mode=expense.billing_mode,
        source=expense.source,
        expense_date=expense.expense_date,
        billing_period_start=expense.billing_period_start,
        billing_period_end=expense.billing_period_end,
        amount=quantize_amount(amount),
        visible_allocated_amount=quantize_amount(visible_amount),
        original_amount_visible=global_reader,
        currency=expense.currency,
        usage_quantity=expense.usage_quantity,
        usage_unit=expense.usage_unit,
        unit_price=expense.unit_price,
        description=expense.description,
        external_reference=expense.external_reference,
        status=expense.status,
        recurring_rule_id=expense.recurring_rule_id,
        visible_attribution=_attribution_text(visible),
        distributions=[serialize_distribution(item) for item in visible],
        created_by=expense.created_by,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


def serialize_rule_distribution(item: RecurringRuleDistribution) -> RecurringRuleDistributionPublic:
    project = item.project
    employee = item.employee
    return RecurringRuleDistributionPublic(
        id=item.id,
        rule_id=item.rule_id,
        project_id=item.project_id,
        project_name=project.name if project else None,
        project_code=project.project_code if project else None,
        employee_id=item.employee_id,
        employee_name=employee.name if employee else None,
        employee_no=employee.employee_no if employee else None,
        allocation_method=item.allocation_method,
        allocation_ratio=item.allocation_ratio,
        allocated_amount=item.allocated_amount,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def serialize_rule(rule: RecurringExpenseRule) -> RecurringRulePublic:
    resource = rule.resource_account
    return RecurringRulePublic(
        id=rule.id,
        name=rule.name,
        expense_type=_type_brief(rule.expense_type),
        resource_account_id=rule.resource_account_id,
        resource_name=resource.resource_name if resource else None,
        frequency=rule.frequency,
        amount=rule.amount,
        currency=rule.currency,
        start_date=rule.start_date,
        end_date=rule.end_date,
        next_run_date=rule.next_run_date,
        is_active=rule.is_active,
        default_distribution_mode=rule.default_distribution_mode,
        description=rule.description,
        distributions=[serialize_rule_distribution(item) for item in rule.distributions],
        created_by=rule.created_by,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def _type_snapshot(expense_type: ExpenseType) -> dict:
    return {
        "id": expense_type.id,
        "code": expense_type.code,
        "name": expense_type.name,
        "category": expense_type.category,
        "description": expense_type.description,
        "is_active": expense_type.is_active,
    }


def _expense_snapshot(expense: ExpenseRecord) -> dict:
    return {
        "id": expense.id,
        "expense_type_id": expense.expense_type_id,
        "resource_account_id": expense.resource_account_id,
        "billing_mode": expense.billing_mode,
        "source": expense.source,
        "expense_date": expense.expense_date.isoformat() if expense.expense_date else None,
        "amount": format(expense.amount, "f"),
        "currency": expense.currency,
        "status": expense.status,
        "distributions": [
            {
                "id": item.id,
                "project_id": item.project_id,
                "employee_id": item.employee_id,
                "allocation_method": item.allocation_method,
                "allocation_ratio": format(item.allocation_ratio, "f") if item.allocation_ratio is not None else None,
                "allocated_amount": format(item.allocated_amount, "f"),
            }
            for item in expense.distributions
        ],
    }


def _rule_snapshot(rule: RecurringExpenseRule) -> dict:
    return {
        "id": rule.id,
        "name": rule.name,
        "expense_type_id": rule.expense_type_id,
        "resource_account_id": rule.resource_account_id,
        "frequency": rule.frequency,
        "amount": format(rule.amount, "f"),
        "currency": rule.currency,
        "start_date": rule.start_date.isoformat(),
        "end_date": rule.end_date.isoformat() if rule.end_date else None,
        "next_run_date": rule.next_run_date.isoformat(),
        "is_active": rule.is_active,
        "default_distribution_mode": rule.default_distribution_mode,
    }


def list_expense_types(db: Session, current_user: CurrentUser, *, include_inactive: bool = False) -> list[ExpenseType]:
    show_inactive = include_inactive and current_user.role == "ADMIN"
    return ExpenseRepository(db).list_types(include_inactive=show_inactive)


def get_expense_type(db: Session, type_id: int) -> ExpenseType:
    expense_type = ExpenseRepository(db).get_type_by_id(type_id)
    if expense_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="费用类型不存在")
    return expense_type


def create_expense_type(
    db: Session,
    payload: ExpenseTypeCreate,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> ExpenseType:
    repo = ExpenseRepository(db)
    code = payload.code.strip()
    if repo.get_type_by_code(code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="费用类型编码已存在")
    expense_type = ExpenseType(
        code=code,
        name=payload.name.strip(),
        category=_validate_enum(payload.category, ExpenseCategory, "无效的费用类别"),
        description=payload.description,
        is_active=True,
    )
    repo.add_type(expense_type)
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="EXPENSE_TYPE_CREATE",
        module="expense",
        target_type="expense_type",
        target_id=expense_type.id,
        after_data=_type_snapshot(expense_type),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(expense_type)
    return expense_type


def update_expense_type(
    db: Session,
    type_id: int,
    payload: ExpenseTypeUpdate,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> ExpenseType:
    expense_type = get_expense_type(db, type_id)
    before = _type_snapshot(expense_type)
    if payload.name is not None:
        expense_type.name = payload.name.strip()
    if payload.category is not None:
        expense_type.category = _validate_enum(payload.category, ExpenseCategory, "无效的费用类别")
    if payload.description is not None:
        expense_type.description = payload.description
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="EXPENSE_TYPE_UPDATE",
        module="expense",
        target_type="expense_type",
        target_id=expense_type.id,
        before_data=before,
        after_data=_type_snapshot(expense_type),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(expense_type)
    return expense_type


def correct_expense_type_code(
    db: Session,
    type_id: int,
    payload: ExpenseTypeCodeChange,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> ExpenseType:
    repo = ExpenseRepository(db)
    expense_type = get_expense_type(db, type_id)
    new_value = normalize_stable_identifier(
        payload.new_code,
        max_length=50,
        invalid_detail="编码格式不合法",
    )
    reject_same(new_value, expense_type.code, "新编码与当前编码一致")
    taken = repo.get_type_by_code(new_value)
    reject_taken(taken.id if taken else None, expense_type.id, "费用类型编码已存在")
    previous = expense_type.code
    expense_type.code = new_value
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="EXPENSE_TYPE_CODE_CHANGE",
        module="expense",
        target_type="expense_type",
        target_id=expense_type.id,
        before_data={"code": previous},
        after_data={"code": new_value},
        ip_address=ip_address,
    )
    commit_stable_identifier(
        db,
        constraint_names=("ix_expense_types_code", "expense_types_code_key"),
        duplicate_detail="费用类型编码已存在",
        failure_detail="费用类型编码修正失败",
    )
    db.refresh(expense_type)
    return expense_type


def set_expense_type_active(
    db: Session,
    type_id: int,
    *,
    is_active: bool,
    operator_user_id: int,
    ip_address: str | None,
) -> ExpenseType:
    expense_type = get_expense_type(db, type_id)
    before = _type_snapshot(expense_type)
    expense_type.is_active = is_active
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="EXPENSE_TYPE_ENABLE" if is_active else "EXPENSE_TYPE_DISABLE",
        module="expense",
        target_type="expense_type",
        target_id=expense_type.id,
        before_data=before,
        after_data=_type_snapshot(expense_type),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(expense_type)
    return expense_type


def _get_active_type(db: Session, type_id: int) -> ExpenseType:
    expense_type = get_expense_type(db, type_id)
    if not expense_type.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="费用类型已停用")
    return expense_type


def _optional_resource(db: Session, resource_id: int | None):
    if resource_id is None:
        return None
    resource = ResourceRepository(db).get_account_by_id(resource_id)
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源账号不存在")
    return resource


def get_readable_expense(db: Session, current_user: CurrentUser, expense_id: int) -> ExpenseRecord:
    if not can_read_expense(db, current_user, expense_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="费用不存在")
    expense = ExpenseRepository(db).get_expense_by_id(expense_id)
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="费用不存在")
    return expense


def list_expenses(
    db: Session,
    current_user: CurrentUser,
    *,
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
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ExpenseRecord], int, int, int]:
    repo = ExpenseRepository(db)
    query = readable_expenses(db, current_user)
    if not status_filter:
        query = query.filter(ExpenseRecord.status == ExpenseStatus.ACTIVE.value)
    query = repo.list_expenses_filtered(
        query,
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
        status=status_filter,
    )
    items, total = repo.paginate(query, page=page, page_size=page_size)
    return items, total, page, page_size


def create_expense(
    db: Session,
    payload: ExpenseCreate,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> ExpenseRecord:
    if payload.source not in {
        ExpenseSource.MANUAL.value,
        ExpenseSource.RECURRING_RULE.value,
        ExpenseSource.IMPORT.value,
    }:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的费用来源")
    _get_active_type(db, payload.expense_type_id)
    _optional_resource(db, payload.resource_account_id)
    amount = _require_positive_amount(payload.amount)
    distributions = validate_and_build_distributions(db, amount, payload.distributions)
    expense = ExpenseRecord(
        expense_type_id=payload.expense_type_id,
        resource_account_id=payload.resource_account_id,
        billing_mode=_validate_enum(payload.billing_mode, BillingMode, "无效的计费方式"),
        source=_validate_enum(payload.source, ExpenseSource, "无效的费用来源"),
        expense_date=payload.expense_date,
        billing_period_start=payload.billing_period_start,
        billing_period_end=payload.billing_period_end,
        amount=amount,
        currency=_validate_currency(payload.currency),
        usage_quantity=quantize_amount(payload.usage_quantity) if payload.usage_quantity is not None else None,
        usage_unit=payload.usage_unit,
        unit_price=to_decimal(payload.unit_price) if payload.unit_price is not None else None,
        description=payload.description,
        external_reference=payload.external_reference,
        status=ExpenseStatus.ACTIVE.value,
        created_by=operator_user_id,
        distributions=distributions,
    )
    ExpenseRepository(db).add_expense(expense)
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="EXPENSE_CREATE",
        module="expense",
        target_type="expense",
        target_id=expense.id,
        after_data=_expense_snapshot(expense),
        ip_address=ip_address,
    )
    db.commit()
    return ExpenseRepository(db).get_expense_by_id(expense.id) or expense


def update_expense(
    db: Session,
    expense_id: int,
    payload: ExpenseUpdate,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> ExpenseRecord:
    expense = ExpenseRepository(db).get_expense_by_id(expense_id)
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="费用不存在")
    if expense.status == ExpenseStatus.VOIDED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已作废费用不能修改")
    before = _expense_snapshot(expense)
    if payload.expense_type_id is not None:
        _get_active_type(db, payload.expense_type_id)
        expense.expense_type_id = payload.expense_type_id
    if "resource_account_id" in payload.model_fields_set:
        _optional_resource(db, payload.resource_account_id)
        expense.resource_account_id = payload.resource_account_id
    if payload.billing_mode is not None:
        expense.billing_mode = _validate_enum(payload.billing_mode, BillingMode, "无效的计费方式")
    if payload.expense_date is not None:
        expense.expense_date = payload.expense_date
    if "billing_period_start" in payload.model_fields_set:
        expense.billing_period_start = payload.billing_period_start
    if "billing_period_end" in payload.model_fields_set:
        expense.billing_period_end = payload.billing_period_end
    if payload.amount is not None:
        expense.amount = _require_positive_amount(payload.amount)
    if payload.currency is not None:
        expense.currency = _validate_currency(payload.currency)
    if "usage_quantity" in payload.model_fields_set:
        expense.usage_quantity = (
            quantize_amount(payload.usage_quantity) if payload.usage_quantity is not None else None
        )
    if "usage_unit" in payload.model_fields_set:
        expense.usage_unit = payload.usage_unit
    if "unit_price" in payload.model_fields_set:
        expense.unit_price = to_decimal(payload.unit_price) if payload.unit_price is not None else None
    if payload.description is not None:
        expense.description = payload.description
    if "external_reference" in payload.model_fields_set:
        expense.external_reference = payload.external_reference
    if payload.distributions is not None:
        expense.distributions.clear()
        db.flush()
        expense.distributions.extend(validate_and_build_distributions(db, expense.amount, payload.distributions))
        write_audit(
            db,
            operator_user_id=operator_user_id,
            action="EXPENSE_DISTRIBUTION_UPDATE",
            module="expense",
            target_type="expense",
            target_id=expense.id,
            before_data=before,
            after_data=None,
            ip_address=ip_address,
        )
    else:
        current_sum = sum((item.allocated_amount for item in expense.distributions), Decimal("0"))
        if not amounts_equal(current_sum, expense.amount):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分摊金额合计必须等于费用金额")
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="EXPENSE_UPDATE",
        module="expense",
        target_type="expense",
        target_id=expense.id,
        before_data=before,
        after_data=_expense_snapshot(expense),
        ip_address=ip_address,
    )
    db.commit()
    return ExpenseRepository(db).get_expense_by_id(expense.id) or expense


def void_expense(
    db: Session,
    expense_id: int,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> ExpenseRecord:
    expense = ExpenseRepository(db).get_expense_by_id(expense_id)
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="费用不存在")
    if expense.status == ExpenseStatus.VOIDED.value:
        return expense
    before = _expense_snapshot(expense)
    expense.status = ExpenseStatus.VOIDED.value
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="EXPENSE_VOID",
        module="expense",
        target_type="expense",
        target_id=expense.id,
        before_data=before,
        after_data=_expense_snapshot(expense),
        ip_address=ip_address,
    )
    db.commit()
    return ExpenseRepository(db).get_expense_by_id(expense.id) or expense


def suggested_distributions(db: Session, resource_account_id: int, amount: Decimal) -> list[SuggestedDistribution]:
    _optional_resource(db, resource_account_id)
    allocations = (
        db.query(ResourceAllocation)
        .options(
            joinedload(ResourceAllocation.project),
            joinedload(ResourceAllocation.employee),
        )
        .filter(
            ResourceAllocation.resource_account_id == resource_account_id,
            ResourceAllocation.is_active.is_(True),
        )
        .order_by(ResourceAllocation.id.asc())
        .all()
    )
    if not allocations:
        return []
    total = _require_positive_amount(amount)
    parts = split_equal(total, len(allocations))
    suggestions: list[SuggestedDistribution] = []
    for allocation, part in zip(allocations, parts, strict=True):
        suggestions.append(
            SuggestedDistribution(
                project_id=allocation.project_id,
                project_name=allocation.project.name if allocation.project else None,
                employee_id=allocation.employee_id,
                employee_name=allocation.employee.name if allocation.employee else None,
                allocation_method=AllocationMethod.EQUAL.value,
                allocation_ratio=None,
                allocated_amount=part,
            )
        )
    return suggestions


def _period_for(frequency: str, run_date: date) -> tuple[date, date]:
    if frequency == RecurringFrequency.MONTHLY.value:
        start = date(run_date.year, run_date.month, 1)
        end = date(run_date.year, run_date.month, monthrange(run_date.year, run_date.month)[1])
        return start, end
    if frequency == RecurringFrequency.QUARTERLY.value:
        quarter = (run_date.month - 1) // 3
        start_month = quarter * 3 + 1
        end_month = start_month + 2
        start = date(run_date.year, start_month, 1)
        end = date(run_date.year, end_month, monthrange(run_date.year, end_month)[1])
        return start, end
    start = date(run_date.year, 1, 1)
    end = date(run_date.year, 12, 31)
    return start, end


def _advance_run_date(run_date: date, frequency: str) -> date:
    if frequency == RecurringFrequency.MONTHLY.value:
        month = run_date.month + 1
        year = run_date.year + (1 if month > 12 else 0)
        month = 1 if month > 12 else month
        day = min(run_date.day, monthrange(year, month)[1])
        return date(year, month, day)
    if frequency == RecurringFrequency.QUARTERLY.value:
        month = run_date.month + 3
        year = run_date.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        day = min(run_date.day, monthrange(year, month)[1])
        return date(year, month, day)
    return date(run_date.year + 1, run_date.month, min(run_date.day, monthrange(run_date.year + 1, run_date.month)[1]))


def list_recurring_rules(db: Session, *, include_inactive: bool = False) -> list[RecurringExpenseRule]:
    return ExpenseRepository(db).list_rules(include_inactive=include_inactive)


def get_recurring_rule(db: Session, rule_id: int) -> RecurringExpenseRule:
    rule = ExpenseRepository(db).get_recurring_by_id(rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="周期规则不存在")
    return rule


def create_recurring_rule(
    db: Session,
    payload: RecurringRuleCreate,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> RecurringExpenseRule:
    _get_active_type(db, payload.expense_type_id)
    _optional_resource(db, payload.resource_account_id)
    amount = _require_positive_amount(payload.amount)
    templates = _validate_rule_templates(db, amount, payload.distributions)
    next_run = payload.next_run_date or payload.start_date
    rule = RecurringExpenseRule(
        name=payload.name.strip(),
        expense_type_id=payload.expense_type_id,
        resource_account_id=payload.resource_account_id,
        frequency=_validate_enum(payload.frequency, RecurringFrequency, "无效的周期频率"),
        amount=amount,
        currency=_validate_currency(payload.currency),
        start_date=payload.start_date,
        end_date=payload.end_date,
        next_run_date=next_run,
        is_active=True,
        default_distribution_mode=_validate_enum(
            payload.default_distribution_mode, AllocationMethod, "无效的分摊方式"
        ),
        description=payload.description,
        created_by=operator_user_id,
        distributions=templates,
    )
    ExpenseRepository(db).add_rule(rule)
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="RECURRING_RULE_CREATE",
        module="expense",
        target_type="recurring_rule",
        target_id=rule.id,
        after_data=_rule_snapshot(rule),
        ip_address=ip_address,
    )
    db.commit()
    return ExpenseRepository(db).get_recurring_by_id(rule.id) or rule


def update_recurring_rule(
    db: Session,
    rule_id: int,
    payload: RecurringRuleUpdate,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> RecurringExpenseRule:
    rule = get_recurring_rule(db, rule_id)
    before = _rule_snapshot(rule)
    if payload.name is not None:
        rule.name = payload.name.strip()
    if payload.expense_type_id is not None:
        _get_active_type(db, payload.expense_type_id)
        rule.expense_type_id = payload.expense_type_id
    if "resource_account_id" in payload.model_fields_set:
        _optional_resource(db, payload.resource_account_id)
        rule.resource_account_id = payload.resource_account_id
    if payload.frequency is not None:
        rule.frequency = _validate_enum(payload.frequency, RecurringFrequency, "无效的周期频率")
    if payload.amount is not None:
        rule.amount = _require_positive_amount(payload.amount)
    if payload.currency is not None:
        rule.currency = _validate_currency(payload.currency)
    if payload.start_date is not None:
        rule.start_date = payload.start_date
    if "end_date" in payload.model_fields_set:
        rule.end_date = payload.end_date
    if payload.next_run_date is not None:
        rule.next_run_date = payload.next_run_date
    if payload.default_distribution_mode is not None:
        rule.default_distribution_mode = _validate_enum(
            payload.default_distribution_mode, AllocationMethod, "无效的分摊方式"
        )
    if payload.description is not None:
        rule.description = payload.description
    if payload.distributions is not None:
        rule.distributions.clear()
        db.flush()
        rule.distributions.extend(_validate_rule_templates(db, rule.amount, payload.distributions))
    else:
        current_sum = sum((item.allocated_amount or Decimal("0") for item in rule.distributions), Decimal("0"))
        if rule.distributions and not amounts_equal(current_sum, rule.amount):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分摊金额合计必须等于费用金额")
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="RECURRING_RULE_UPDATE",
        module="expense",
        target_type="recurring_rule",
        target_id=rule.id,
        before_data=before,
        after_data=_rule_snapshot(rule),
        ip_address=ip_address,
    )
    db.commit()
    return ExpenseRepository(db).get_recurring_by_id(rule.id) or rule


def set_recurring_rule_active(
    db: Session,
    rule_id: int,
    *,
    is_active: bool,
    operator_user_id: int,
    ip_address: str | None,
) -> RecurringExpenseRule:
    rule = get_recurring_rule(db, rule_id)
    before = _rule_snapshot(rule)
    rule.is_active = is_active
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="RECURRING_RULE_ENABLE" if is_active else "RECURRING_RULE_DISABLE",
        module="expense",
        target_type="recurring_rule",
        target_id=rule.id,
        before_data=before,
        after_data=_rule_snapshot(rule),
        ip_address=ip_address,
    )
    db.commit()
    return ExpenseRepository(db).get_recurring_by_id(rule.id) or rule


def generate_recurring_expenses(
    db: Session,
    *,
    operator_user_id: int | None,
    ip_address: str | None,
    as_of: date | None = None,
) -> RecurringGenerateResult:
    as_of = as_of or business_today(db)
    repo = ExpenseRepository(db)
    generated_ids: list[int] = []
    skipped = 0
    for rule in repo.list_due_rules(as_of):
        while (
            rule.is_active
            and rule.next_run_date <= as_of
            and (rule.end_date is None or rule.next_run_date <= rule.end_date)
        ):
            period_start, period_end = _period_for(rule.frequency, rule.next_run_date)
            existing = repo.existing_generated(rule.id, period_start)
            if existing is not None:
                skipped += 1
                rule.next_run_date = _advance_run_date(rule.next_run_date, rule.frequency)
                continue
            template_inputs = [
                ExpenseDistributionInput(
                    project_id=item.project_id,
                    employee_id=item.employee_id,
                    allocation_method=item.allocation_method,
                    allocation_ratio=item.allocation_ratio,
                    allocated_amount=item.allocated_amount,
                )
                for item in rule.distributions
            ]
            distributions = validate_and_build_distributions(db, rule.amount, template_inputs)
            expense = ExpenseRecord(
                expense_type_id=rule.expense_type_id,
                resource_account_id=rule.resource_account_id,
                billing_mode=BillingMode.RECURRING.value,
                source=ExpenseSource.RECURRING_RULE.value,
                expense_date=period_start,
                billing_period_start=period_start,
                billing_period_end=period_end,
                amount=rule.amount,
                currency=rule.currency,
                description=rule.name,
                status=ExpenseStatus.ACTIVE.value,
                recurring_rule_id=rule.id,
                created_by=operator_user_id,
                distributions=distributions,
            )
            try:
                with db.begin_nested():
                    repo.add_expense(expense)
                    db.flush()
            except IntegrityError:
                skipped += 1
                rule.next_run_date = _advance_run_date(rule.next_run_date, rule.frequency)
                continue
            generated_ids.append(expense.id)
            rule.next_run_date = _advance_run_date(rule.next_run_date, rule.frequency)
            write_audit(
                db,
                operator_user_id=operator_user_id,
                action="RECURRING_EXPENSE_GENERATE",
                module="expense",
                target_type="expense",
                target_id=expense.id,
                after_data=_expense_snapshot(expense),
                ip_address=ip_address,
            )
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="RECURRING_EXPENSE_GENERATE",
        module="expense",
        target_type="recurring_generate",
        target_id="batch",
        after_data={"generated_ids": generated_ids, "skipped_count": skipped, "as_of": as_of.isoformat()},
        ip_address=ip_address,
    )
    db.commit()
    return RecurringGenerateResult(
        generated_count=len(generated_ids),
        skipped_count=skipped,
        generated_ids=generated_ids,
    )
