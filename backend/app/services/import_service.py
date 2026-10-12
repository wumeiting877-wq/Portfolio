from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Iterator

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.enums import BillingMode, EmploymentStatus, ExpenseSource
from app.models.expense_type import ExpenseType
from app.models.project import Project
from app.models.resource_account import ResourceAccount
from app.models.resource_type import ResourceType
from app.permissions.dependencies import CurrentUser
from app.schemas.employee import EmployeeCreate, normalize_optional_email
from app.schemas.expense import ExpenseCreate, ExpenseDistributionInput
from app.schemas.project import ProjectCreate
from app.schemas.resource import ResourceAllocationCreate, ResourceCreate, ResourceTypeCreate
from app.services.audit_service import write_audit
from app.services.employee_service import create_employee
from app.services.excel_io import TEMPLATE_COLUMNS, parse_workbook
from app.services.expense_service import (
    _require_positive_amount,
    _validate_currency,
    _validate_enum,
    create_expense,
    validate_and_build_distributions,
)
from app.services.project_service import _validate_dates, _validate_status, add_or_restore_member, create_project
from app.services.resource_service import (
    _validate_allocation_targets,
    _validate_category,
    _validate_resource_status,
    add_or_restore_allocation,
    create_resource,
    create_resource_type,
)


class ImportRowError(Exception):
    def __init__(self, row: int, field: str, message: str) -> None:
        self.row = row
        self.field = field
        self.message = message
        super().__init__(message)


def _http_message(exc: HTTPException) -> str:
    detail = exc.detail
    if isinstance(detail, str):
        return detail
    return "校验失败"


@contextmanager
def deferred_commit(db: Session) -> Iterator[None]:
    original = db.commit
    db.commit = db.flush  # type: ignore[method-assign]
    try:
        yield
        db.commit = original  # type: ignore[method-assign]
        original()
    except Exception:
        db.commit = original  # type: ignore[method-assign]
        db.rollback()
        raise


def _required(row: int, values: dict[str, str], field: str) -> str:
    value = (values.get(field) or "").strip()
    if not value:
        raise ImportRowError(row, field, "必填")
    return value


def _optional(values: dict[str, str], field: str) -> str | None:
    value = (values.get(field) or "").strip()
    return value or None


def _parse_date(row: int, field: str, raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError as exc:
        raise ImportRowError(row, field, "日期必须为 YYYY-MM-DD") from exc


def _parse_decimal(row: int, field: str, raw: str | None) -> Decimal | None:
    if raw is None or raw == "":
        return None
    try:
        return Decimal(str(raw))
    except (InvalidOperation, ValueError) as exc:
        raise ImportRowError(row, field, "金额必须为数字") from exc


def _employee_by_no(db: Session, employee_no: str) -> Employee | None:
    return db.query(Employee).filter(Employee.employee_no == employee_no).first()


def _project_by_code(db: Session, project_code: str) -> Project | None:
    return db.query(Project).filter(Project.project_code == project_code).first()


def _resource_type_by_code(db: Session, code: str) -> ResourceType | None:
    return db.query(ResourceType).filter(ResourceType.code == code).first()


def _resource_by_name(db: Session, name: str) -> ResourceAccount | None:
    return db.query(ResourceAccount).filter(ResourceAccount.resource_name == name).first()


def _expense_type_by_code(db: Session, code: str) -> ExpenseType | None:
    return db.query(ExpenseType).filter(ExpenseType.code == code).first()


def _validate_employee(db: Session, row: int, values: dict[str, str], seen: set[str]) -> dict[str, Any]:
    employee_no = _required(row, values, "employee_no")
    name = _required(row, values, "name")
    if employee_no in seen:
        raise ImportRowError(row, "employee_no", "工号在本批次重复")
    seen.add(employee_no)
    if _employee_by_no(db, employee_no):
        raise ImportRowError(row, "employee_no", "工号已存在")
    email = _optional(values, "email")
    if email:
        try:
            email = normalize_optional_email(email)
        except ValueError as exc:
            raise ImportRowError(row, "email", "邮箱格式不正确") from exc
    status_value = _optional(values, "employment_status") or EmploymentStatus.ACTIVE.value
    try:
        status_value = EmploymentStatus(status_value).value
    except ValueError as exc:
        raise ImportRowError(row, "employment_status", "无效的人员状态") from exc
    return {
        "payload": EmployeeCreate(
            employee_no=employee_no,
            name=name,
            department=_optional(values, "department"),
            position=_optional(values, "position"),
            email=email,
            phone=_optional(values, "phone"),
            remark=_optional(values, "remark"),
        ),
        "employment_status": status_value,
    }


def _persist_employee(db: Session, current_user: CurrentUser, ip: str | None, prepared: dict[str, Any]) -> None:
    employee = create_employee(
        db, prepared["payload"], operator_user_id=current_user.id, ip_address=ip
    )
    if prepared["employment_status"] != EmploymentStatus.ACTIVE.value:
        employee.employment_status = prepared["employment_status"]
        db.add(employee)
        db.flush()


def _validate_project(db: Session, row: int, values: dict[str, str], seen: set[str]) -> dict[str, Any]:
    project_code = _required(row, values, "project_code")
    name = _required(row, values, "name")
    manager_no = _required(row, values, "manager_employee_no")
    if project_code in seen:
        raise ImportRowError(row, "project_code", "项目编码在本批次重复")
    seen.add(project_code)
    if _project_by_code(db, project_code):
        raise ImportRowError(row, "project_code", "项目编码已存在")
    manager = _employee_by_no(db, manager_no)
    if manager is None:
        raise ImportRowError(row, "manager_employee_no", "负责人不存在")
    if manager.employment_status != EmploymentStatus.ACTIVE.value:
        raise ImportRowError(row, "manager_employee_no", "负责人必须是在职人员")
    status_value = _optional(values, "status") or "PLANNING"
    start_date = _parse_date(row, "start_date", _optional(values, "start_date"))
    end_date = _parse_date(row, "end_date", _optional(values, "end_date"))
    try:
        status_value = _validate_status(status_value)
        _validate_dates(start_date, end_date)
    except HTTPException as exc:
        raise ImportRowError(row, "status", _http_message(exc)) from exc
    return {
        "payload": ProjectCreate(
            project_code=project_code,
            name=name,
            manager_employee_id=manager.id,
            status=status_value,
            description=_optional(values, "description"),
            start_date=start_date,
            end_date=end_date,
        )
    }


def _persist_project(db: Session, current_user: CurrentUser, ip: str | None, prepared: dict[str, Any]) -> None:
    create_project(db, prepared["payload"], operator_user_id=current_user.id, ip_address=ip)


def _validate_project_member(db: Session, row: int, values: dict[str, str], seen: set[str]) -> dict[str, Any]:
    project_code = _required(row, values, "project_code")
    employee_no = _required(row, values, "employee_no")
    key = f"{project_code}:{employee_no}"
    if key in seen:
        raise ImportRowError(row, "employee_no", "同一项目成员在本批次重复")
    seen.add(key)
    project = _project_by_code(db, project_code)
    if project is None:
        raise ImportRowError(row, "project_code", "项目不存在")
    employee = _employee_by_no(db, employee_no)
    if employee is None:
        raise ImportRowError(row, "employee_no", "人员不存在")
    return {
        "project_id": project.id,
        "employee_id": employee.id,
        "member_role": _optional(values, "member_role") or "MEMBER",
    }


def _persist_project_member(db: Session, current_user: CurrentUser, ip: str | None, prepared: dict[str, Any]) -> None:
    add_or_restore_member(
        db,
        prepared["project_id"],
        prepared["employee_id"],
        prepared["member_role"],
        operator_user_id=current_user.id,
        ip_address=ip,
    )


def _validate_resource_type(db: Session, row: int, values: dict[str, str], seen: set[str]) -> dict[str, Any]:
    code = _required(row, values, "code")
    name = _required(row, values, "name")
    if code in seen:
        raise ImportRowError(row, "code", "类型编码在本批次重复")
    seen.add(code)
    if _resource_type_by_code(db, code):
        raise ImportRowError(row, "code", "资源类型编码已存在")
    category = _optional(values, "category") or "OTHER"
    try:
        category = _validate_category(category)
    except HTTPException as exc:
        raise ImportRowError(row, "category", _http_message(exc)) from exc
    return {
        "payload": ResourceTypeCreate(
            code=code,
            name=name,
            category=category,
            description=_optional(values, "description"),
        )
    }


def _persist_resource_type(db: Session, current_user: CurrentUser, ip: str | None, prepared: dict[str, Any]) -> None:
    create_resource_type(db, prepared["payload"], operator_user_id=current_user.id, ip_address=ip)


def _validate_resource(db: Session, row: int, values: dict[str, str], seen: set[str]) -> dict[str, Any]:
    resource_name = _required(row, values, "resource_name")
    type_code = _required(row, values, "resource_type_code")
    if resource_name in seen:
        raise ImportRowError(row, "resource_name", "资源名称在本批次重复")
    seen.add(resource_name)
    resource_type = _resource_type_by_code(db, type_code)
    if resource_type is None:
        raise ImportRowError(row, "resource_type_code", "资源类型不存在")
    if not resource_type.is_active:
        raise ImportRowError(row, "resource_type_code", "资源类型已停用")
    status_value = _optional(values, "status") or "ACTIVE"
    try:
        status_value = _validate_resource_status(status_value)
    except HTTPException as exc:
        raise ImportRowError(row, "status", _http_message(exc)) from exc
    return {
        "payload": ResourceCreate(
            resource_type_id=resource_type.id,
            resource_name=resource_name,
            provider=_optional(values, "provider"),
            account_identifier=_optional(values, "account_identifier"),
            plan_name=_optional(values, "plan_name"),
            status=status_value,
            purchased_at=_parse_date(row, "purchased_at", _optional(values, "purchased_at")),
            activated_at=_parse_date(row, "activated_at", _optional(values, "activated_at")),
            expires_at=_parse_date(row, "expires_at", _optional(values, "expires_at")),
            remark=_optional(values, "remark"),
        )
    }


def _persist_resource(db: Session, current_user: CurrentUser, ip: str | None, prepared: dict[str, Any]) -> None:
    create_resource(db, prepared["payload"], operator_user_id=current_user.id, ip_address=ip)


def _validate_allocation(db: Session, row: int, values: dict[str, str], seen: set[str]) -> dict[str, Any]:
    resource_name = _required(row, values, "resource_name")
    project_code = _optional(values, "project_code")
    employee_no = _optional(values, "employee_no")
    key = f"{resource_name}:{project_code}:{employee_no}"
    if key in seen:
        raise ImportRowError(row, "resource_name", "分配关系在本批次重复")
    seen.add(key)
    resource = _resource_by_name(db, resource_name)
    if resource is None:
        raise ImportRowError(row, "resource_name", "资源不存在")
    project_id = None
    employee_id = None
    if project_code:
        project = _project_by_code(db, project_code)
        if project is None:
            raise ImportRowError(row, "project_code", "项目不存在")
        project_id = project.id
    if employee_no:
        employee = _employee_by_no(db, employee_no)
        if employee is None:
            raise ImportRowError(row, "employee_no", "人员不存在")
        employee_id = employee.id
    payload = ResourceAllocationCreate(
        project_id=project_id,
        employee_id=employee_id,
        remark=_optional(values, "remark"),
    )
    try:
        _validate_allocation_targets(db, payload.project_id, payload.employee_id)
    except HTTPException as exc:
        raise ImportRowError(row, "project_code", _http_message(exc)) from exc
    return {
        "resource_id": resource.id,
        "payload": payload,
    }


def _persist_allocation(db: Session, current_user: CurrentUser, ip: str | None, prepared: dict[str, Any]) -> None:
    add_or_restore_allocation(
        db,
        prepared["resource_id"],
        prepared["payload"],
        operator_user_id=current_user.id,
        ip_address=ip,
    )


def _validate_expense(db: Session, row: int, values: dict[str, str], seen: set[str]) -> dict[str, Any]:
    type_code = _required(row, values, "expense_type_code")
    billing_mode = _required(row, values, "billing_mode")
    expense_date = _parse_date(row, "expense_date", _required(row, values, "expense_date"))
    amount = _parse_decimal(row, "amount", _required(row, values, "amount"))
    currency = _required(row, values, "currency")
    expense_type = _expense_type_by_code(db, type_code)
    if expense_type is None:
        raise ImportRowError(row, "expense_type_code", "费用类型不存在")
    if not expense_type.is_active:
        raise ImportRowError(row, "expense_type_code", "费用类型已停用")
    resource_id = None
    resource_name = _optional(values, "resource_name")
    if resource_name:
        resource = _resource_by_name(db, resource_name)
        if resource is None:
            raise ImportRowError(row, "resource_name", "资源不存在")
        resource_id = resource.id
    project_code = _optional(values, "project_code")
    employee_no = _optional(values, "employee_no")
    project_id = None
    employee_id = None
    if project_code:
        project = _project_by_code(db, project_code)
        if project is None:
            raise ImportRowError(row, "project_code", "项目不存在")
        project_id = project.id
    if employee_no:
        employee = _employee_by_no(db, employee_no)
        if employee is None:
            raise ImportRowError(row, "employee_no", "人员不存在")
        employee_id = employee.id
    allocated = _parse_decimal(row, "allocated_amount", _optional(values, "allocated_amount"))
    try:
        amount = _require_positive_amount(amount or Decimal("0"))
        currency = _validate_currency(currency)
        billing_mode = _validate_enum(billing_mode, BillingMode, "无效的计费方式")
        distributions = [
            ExpenseDistributionInput(
                project_id=project_id,
                employee_id=employee_id,
                allocation_method=_optional(values, "allocation_method") or "DIRECT",
                allocated_amount=allocated if allocated is not None else amount,
            )
        ]
        validate_and_build_distributions(db, amount, distributions)
    except HTTPException as exc:
        raise ImportRowError(row, "amount", _http_message(exc)) from exc
    return {
        "payload": ExpenseCreate(
            expense_type_id=expense_type.id,
            resource_account_id=resource_id,
            billing_mode=billing_mode,
            source=ExpenseSource.IMPORT.value,
            expense_date=expense_date or date.today(),
            billing_period_start=_parse_date(row, "billing_period_start", _optional(values, "billing_period_start")),
            billing_period_end=_parse_date(row, "billing_period_end", _optional(values, "billing_period_end")),
            amount=amount,
            currency=currency,
            description=_optional(values, "description"),
            external_reference=_optional(values, "external_reference"),
            distributions=distributions,
        )
    }


def _persist_expense(db: Session, current_user: CurrentUser, ip: str | None, prepared: dict[str, Any]) -> None:
    create_expense(db, prepared["payload"], operator_user_id=current_user.id, ip_address=ip)


HANDLERS: dict[str, tuple[Callable, Callable]] = {
    "employees": (_validate_employee, _persist_employee),
    "projects": (_validate_project, _persist_project),
    "project_members": (_validate_project_member, _persist_project_member),
    "resource_types": (_validate_resource_type, _persist_resource_type),
    "resources": (_validate_resource, _persist_resource),
    "resource_allocations": (_validate_allocation, _persist_allocation),
    "expenses": (_validate_expense, _persist_expense),
}


def _prepare_rows(
    db: Session, import_type: str, rows: list[tuple[int, dict[str, str]]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    validator, _persist = HANDLERS[import_type]
    prepared: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    seen: set[str] = set()
    known = {field for _, _, _, _, field in TEMPLATE_COLUMNS[import_type]}
    for excel_row, values in rows:
        unknown = [key for key in values if key not in known]
        if unknown:
            errors.append({"row": excel_row, "field": unknown[0], "message": "无法识别的列"})
            continue
        try:
            prepared.append(validator(db, excel_row, values, seen))
        except ImportRowError as exc:
            errors.append({"row": exc.row, "field": exc.field, "message": exc.message})
        except HTTPException as exc:
            errors.append({"row": excel_row, "field": "-", "message": _http_message(exc)})
        except Exception as exc:  # validation should be explicit; keep row-level
            errors.append({"row": excel_row, "field": "-", "message": str(exc)})
    return prepared, errors


def preview_import(db: Session, import_type: str, content: bytes) -> dict[str, Any]:
    rows = parse_workbook(import_type, content)
    prepared, errors = _prepare_rows(db, import_type, rows)
    return {
        "import_type": import_type,
        "total_rows": len(rows),
        "valid_rows": len(prepared),
        "invalid_rows": len(errors),
        "errors": errors,
    }


def commit_import(
    db: Session,
    import_type: str,
    content: bytes,
    *,
    current_user: CurrentUser,
    ip_address: str | None,
) -> dict[str, Any]:
    rows = parse_workbook(import_type, content)
    prepared, errors = _prepare_rows(db, import_type, rows)
    if errors:
        db.rollback()
        return {
            "import_type": import_type,
            "committed": False,
            "created_count": 0,
            "total_rows": len(rows),
            "valid_rows": len(prepared),
            "invalid_rows": len(errors),
            "errors": errors,
        }
    _, persist = HANDLERS[import_type]
    created = 0
    try:
        with deferred_commit(db):
            for item in prepared:
                persist(db, current_user, ip_address, item)
                created += 1
            write_audit(
                db,
                operator_user_id=current_user.id,
                action="IMPORT_COMMIT",
                module="import",
                target_type=import_type,
                target_id=str(created),
                after_data={"import_type": import_type, "created_count": created, "total_rows": len(rows)},
                ip_address=ip_address,
            )
    except HTTPException as exc:
        return {
            "import_type": import_type,
            "committed": False,
            "created_count": 0,
            "total_rows": len(rows),
            "valid_rows": 0,
            "invalid_rows": 1,
            "errors": [{"row": 0, "field": "-", "message": _http_message(exc)}],
        }
    return {
        "import_type": import_type,
        "committed": True,
        "created_count": created,
        "total_rows": len(rows),
        "valid_rows": created,
        "invalid_rows": 0,
        "errors": [],
    }
