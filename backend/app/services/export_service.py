from __future__ import annotations

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.audit_log import AuditLog
from app.models.employee import Employee
from app.models.enums import ExpenseStatus, RoleCode
from app.models.expense_distribution import ExpenseDistribution
from app.models.expense_record import ExpenseRecord
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.resource_account import ResourceAccount
from app.models.resource_allocation import ResourceAllocation
from app.models.user import User
from app.permissions.dependencies import CurrentUser
from app.permissions.expense_scope import readable_distributions, readable_expenses
from app.permissions.project_scope import readable_projects
from app.permissions.resource_scope import readable_allocations, readable_resources
from app.repositories.statistics_repository import StatisticsRepository
from app.services.audit_service import public_audit_payload
from app.services.excel_io import new_export_workbook, workbook_bytes, write_cell, write_header
from app.services.settings_service import business_today, get_expiring_days
from app.services.statistics_service import get_employee_costs, get_project_costs, get_resource_type_costs

EXPORT_TYPES = {
    "employees": {RoleCode.ADMIN.value},
    "projects": {RoleCode.ADMIN.value, RoleCode.BOSS.value, RoleCode.PROJECT_MANAGER.value},
    "project_members": {RoleCode.ADMIN.value, RoleCode.PROJECT_MANAGER.value},
    "resources": {
        RoleCode.ADMIN.value,
        RoleCode.BOSS.value,
        RoleCode.PROJECT_MANAGER.value,
        RoleCode.MEMBER.value,
    },
    "resource_allocations": {RoleCode.ADMIN.value, RoleCode.PROJECT_MANAGER.value},
    "expenses": {
        RoleCode.ADMIN.value,
        RoleCode.BOSS.value,
        RoleCode.PROJECT_MANAGER.value,
        RoleCode.MEMBER.value,
    },
    "expense_distributions": {RoleCode.ADMIN.value, RoleCode.PROJECT_MANAGER.value},
    "project_costs": {RoleCode.ADMIN.value, RoleCode.BOSS.value, RoleCode.PROJECT_MANAGER.value},
    "employee_costs": {RoleCode.ADMIN.value, RoleCode.BOSS.value, RoleCode.PROJECT_MANAGER.value},
    "resource_type_costs": {RoleCode.ADMIN.value, RoleCode.BOSS.value},
    "expiring_resources": {
        RoleCode.ADMIN.value,
        RoleCode.BOSS.value,
        RoleCode.PROJECT_MANAGER.value,
        RoleCode.MEMBER.value,
    },
    "idle_resources": {RoleCode.ADMIN.value, RoleCode.BOSS.value},
    "audit_logs": {RoleCode.ADMIN.value},
}


def ensure_export_allowed(export_type: str, role: str) -> str:
    allowed = EXPORT_TYPES.get(export_type)
    if allowed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="不支持的导出类型")
    if role not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限")
    return export_type


def _filename(export_type: str) -> str:
    stamp = date.today().isoformat()
    return f"{export_type}_{stamp}.xlsx"


def build_export(
    db: Session,
    current_user: CurrentUser,
    export_type: str,
    *,
    date_from: date | None,
    date_to: date | None,
    project_id: int | None,
    currency: str | None,
) -> tuple[bytes, str]:
    ensure_export_allowed(export_type, current_user.role)
    builder = {
        "employees": _export_employees,
        "projects": _export_projects,
        "project_members": _export_project_members,
        "resources": _export_resources,
        "resource_allocations": _export_allocations,
        "expenses": _export_expenses,
        "expense_distributions": _export_distributions,
        "project_costs": _export_project_costs,
        "employee_costs": _export_employee_costs,
        "resource_type_costs": _export_resource_type_costs,
        "expiring_resources": _export_expiring,
        "idle_resources": _export_idle,
        "audit_logs": _export_audit_logs,
    }[export_type]
    content = builder(
        db,
        current_user,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        currency=currency,
    )
    return content, _filename(export_type)


def _export_employees(db: Session, current_user: CurrentUser, **_: object) -> bytes:
    workbook, sheet = new_export_workbook("employees")
    headers = ["id", "employee_no", "name", "department", "position", "email", "phone", "employment_status"]
    write_header(sheet, headers)
    rows = db.query(Employee).order_by(Employee.id.asc()).all()
    for index, item in enumerate(rows, start=2):
        write_cell(sheet, index, 1, item.id)
        write_cell(sheet, index, 2, item.employee_no)
        write_cell(sheet, index, 3, item.name)
        write_cell(sheet, index, 4, item.department)
        write_cell(sheet, index, 5, item.position)
        write_cell(sheet, index, 6, item.email)
        write_cell(sheet, index, 7, item.phone)
        write_cell(sheet, index, 8, item.employment_status)
    return workbook_bytes(workbook)


def _export_projects(
    db: Session,
    current_user: CurrentUser,
    *,
    project_id: int | None,
    **_: object,
) -> bytes:
    workbook, sheet = new_export_workbook("projects")
    write_header(sheet, ["id", "project_code", "name", "manager_employee_no", "status", "start_date", "end_date"])
    query = readable_projects(db, current_user).options(joinedload(Project.manager)).order_by(Project.id.asc())
    if project_id is not None:
        query = query.filter(Project.id == project_id)
    for index, item in enumerate(query.all(), start=2):
        write_cell(sheet, index, 1, item.id)
        write_cell(sheet, index, 2, item.project_code)
        write_cell(sheet, index, 3, item.name)
        write_cell(sheet, index, 4, item.manager.employee_no if item.manager else None)
        write_cell(sheet, index, 5, item.status)
        write_cell(sheet, index, 6, item.start_date, as_date=True)
        write_cell(sheet, index, 7, item.end_date, as_date=True)
    return workbook_bytes(workbook)


def _export_project_members(
    db: Session,
    current_user: CurrentUser,
    *,
    project_id: int | None,
    **_: object,
) -> bytes:
    workbook, sheet = new_export_workbook("project_members")
    write_header(sheet, ["project_code", "project_name", "employee_no", "name", "member_role", "is_active"])
    project_ids = readable_projects(db, current_user).with_entities(Project.id)
    query = (
        db.query(ProjectMember)
        .options(joinedload(ProjectMember.project), joinedload(ProjectMember.employee))
        .filter(ProjectMember.project_id.in_(project_ids))
        .order_by(ProjectMember.id.asc())
    )
    if project_id is not None:
        query = query.filter(ProjectMember.project_id == project_id)
    for index, item in enumerate(query.all(), start=2):
        write_cell(sheet, index, 1, item.project.project_code if item.project else None)
        write_cell(sheet, index, 2, item.project.name if item.project else None)
        write_cell(sheet, index, 3, item.employee.employee_no if item.employee else None)
        write_cell(sheet, index, 4, item.employee.name if item.employee else None)
        write_cell(sheet, index, 5, item.member_role)
        write_cell(sheet, index, 6, "Y" if item.is_active else "N")
    return workbook_bytes(workbook)


def _export_resources(
    db: Session,
    current_user: CurrentUser,
    *,
    project_id: int | None,
    **_: object,
) -> bytes:
    workbook, sheet = new_export_workbook("resources")
    write_header(
        sheet,
        ["id", "resource_name", "resource_type_code", "provider", "account_identifier", "status", "expires_at"],
    )
    query = readable_resources(db, current_user).options(joinedload(ResourceAccount.resource_type))
    if project_id is not None:
        allocated = db.query(ResourceAllocation.resource_account_id).filter(
            ResourceAllocation.is_active.is_(True),
            ResourceAllocation.project_id == project_id,
        )
        query = query.filter(ResourceAccount.id.in_(allocated))
    for index, item in enumerate(query.order_by(ResourceAccount.id.asc()).all(), start=2):
        write_cell(sheet, index, 1, item.id)
        write_cell(sheet, index, 2, item.resource_name)
        write_cell(sheet, index, 3, item.resource_type.code if item.resource_type else None)
        write_cell(sheet, index, 4, item.provider)
        write_cell(sheet, index, 5, item.account_identifier)
        write_cell(sheet, index, 6, item.status)
        write_cell(sheet, index, 7, item.expires_at, as_date=True)
    return workbook_bytes(workbook)


def _export_allocations(
    db: Session,
    current_user: CurrentUser,
    *,
    project_id: int | None,
    **_: object,
) -> bytes:
    workbook, sheet = new_export_workbook("resource_allocations")
    write_header(sheet, ["resource_name", "project_code", "employee_no", "is_active", "allocated_at", "released_at"])
    query = readable_allocations(db, current_user).options(
        joinedload(ResourceAllocation.resource),
        joinedload(ResourceAllocation.project),
        joinedload(ResourceAllocation.employee),
    )
    if project_id is not None:
        query = query.filter(ResourceAllocation.project_id == project_id)
    for index, item in enumerate(query.order_by(ResourceAllocation.id.asc()).all(), start=2):
        write_cell(sheet, index, 1, item.resource.resource_name if item.resource else None)
        write_cell(sheet, index, 2, item.project.project_code if item.project else None)
        write_cell(sheet, index, 3, item.employee.employee_no if item.employee else None)
        write_cell(sheet, index, 4, "Y" if item.is_active else "N")
        write_cell(sheet, index, 5, item.allocated_at.date() if item.allocated_at else None, as_date=True)
        write_cell(sheet, index, 6, item.released_at.date() if item.released_at else None, as_date=True)
    return workbook_bytes(workbook)


def _export_expenses(
    db: Session,
    current_user: CurrentUser,
    *,
    date_from: date | None,
    date_to: date | None,
    project_id: int | None,
    currency: str | None,
) -> bytes:
    workbook, sheet = new_export_workbook("expenses")
    write_header(
        sheet,
        ["id", "expense_date", "expense_type", "description", "amount", "currency", "status", "source"],
    )
    query = readable_expenses(db, current_user).options(joinedload(ExpenseRecord.expense_type))
    query = query.filter(ExpenseRecord.status == ExpenseStatus.ACTIVE.value)
    if date_from is not None:
        query = query.filter(ExpenseRecord.expense_date >= date_from)
    if date_to is not None:
        query = query.filter(ExpenseRecord.expense_date <= date_to)
    if currency:
        query = query.filter(ExpenseRecord.currency == currency)
    if project_id is not None:
        matched = db.query(ExpenseDistribution.expense_record_id).filter(
            ExpenseDistribution.project_id == project_id
        )
        query = query.filter(ExpenseRecord.id.in_(matched))
        scoped_ids = readable_expenses(db, current_user).with_entities(ExpenseRecord.id)
        query = query.filter(ExpenseRecord.id.in_(scoped_ids))
    for index, item in enumerate(query.order_by(ExpenseRecord.id.asc()).all(), start=2):
        write_cell(sheet, index, 1, item.id)
        write_cell(sheet, index, 2, item.expense_date, as_date=True)
        write_cell(sheet, index, 3, item.expense_type.name if item.expense_type else None)
        write_cell(sheet, index, 4, item.description)
        write_cell(sheet, index, 5, item.amount, money=True)
        write_cell(sheet, index, 6, item.currency)
        write_cell(sheet, index, 7, item.status)
        write_cell(sheet, index, 8, item.source)
    return workbook_bytes(workbook)


def _export_distributions(
    db: Session,
    current_user: CurrentUser,
    *,
    date_from: date | None,
    date_to: date | None,
    project_id: int | None,
    currency: str | None,
) -> bytes:
    workbook, sheet = new_export_workbook("expense_distributions")
    write_header(
        sheet,
        ["expense_id", "expense_date", "project_code", "employee_no", "allocated_amount", "currency", "method"],
    )
    query = readable_distributions(db, current_user).join(
        ExpenseRecord, ExpenseRecord.id == ExpenseDistribution.expense_record_id
    ).options(
        joinedload(ExpenseDistribution.project),
        joinedload(ExpenseDistribution.employee),
        joinedload(ExpenseDistribution.expense_record),
    )
    query = query.filter(ExpenseRecord.status == ExpenseStatus.ACTIVE.value)
    if date_from is not None:
        query = query.filter(ExpenseRecord.expense_date >= date_from)
    if date_to is not None:
        query = query.filter(ExpenseRecord.expense_date <= date_to)
    if currency:
        query = query.filter(ExpenseRecord.currency == currency)
    if project_id is not None:
        query = query.filter(ExpenseDistribution.project_id == project_id)
    for index, item in enumerate(query.order_by(ExpenseDistribution.id.asc()).all(), start=2):
        record = item.expense_record
        write_cell(sheet, index, 1, item.expense_record_id)
        write_cell(sheet, index, 2, record.expense_date if record else None, as_date=True)
        write_cell(sheet, index, 3, item.project.project_code if item.project else None)
        write_cell(sheet, index, 4, item.employee.employee_no if item.employee else None)
        write_cell(sheet, index, 5, item.allocated_amount, money=True)
        write_cell(sheet, index, 6, record.currency if record else None)
        write_cell(sheet, index, 7, item.allocation_method)
    return workbook_bytes(workbook)


def _export_project_costs(
    db: Session,
    current_user: CurrentUser,
    *,
    date_from: date | None,
    date_to: date | None,
    project_id: int | None,
    **_: object,
) -> bytes:
    result = get_project_costs(
        db, current_user, date_from=date_from, date_to=date_to, project_id=project_id, limit=1000
    )
    workbook, sheet = new_export_workbook("project_costs")
    write_header(sheet, ["project_id", "project_name", "allocated_amount", "currency"])
    for index, item in enumerate(result.items, start=2):
        write_cell(sheet, index, 1, item.project_id)
        write_cell(sheet, index, 2, item.project_name)
        write_cell(sheet, index, 3, item.allocated_amount, money=True)
        write_cell(sheet, index, 4, item.currency)
    return workbook_bytes(workbook)


def _export_employee_costs(
    db: Session,
    current_user: CurrentUser,
    *,
    date_from: date | None,
    date_to: date | None,
    project_id: int | None,
    **_: object,
) -> bytes:
    result = get_employee_costs(
        db,
        current_user,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        employee_id=None,
        limit=1000,
    )
    workbook, sheet = new_export_workbook("employee_costs")
    write_header(sheet, ["employee_no", "employee_name", "allocated_amount", "currency"])
    for index, item in enumerate(result.items, start=2):
        write_cell(sheet, index, 1, item.employee_no)
        write_cell(sheet, index, 2, item.employee_name)
        write_cell(sheet, index, 3, item.allocated_amount, money=True)
        write_cell(sheet, index, 4, item.currency)
    return workbook_bytes(workbook)


def _export_resource_type_costs(
    db: Session,
    current_user: CurrentUser,
    *,
    date_from: date | None,
    date_to: date | None,
    project_id: int | None,
    **_: object,
) -> bytes:
    result = get_resource_type_costs(
        db,
        current_user,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        employee_id=None,
        limit=1000,
    )
    workbook, sheet = new_export_workbook("resource_type_costs")
    write_header(sheet, ["resource_type_code", "resource_type_name", "allocated_amount", "currency"])
    for index, item in enumerate(result.items, start=2):
        write_cell(sheet, index, 1, item.resource_type_code)
        write_cell(sheet, index, 2, item.resource_type_name)
        write_cell(sheet, index, 3, item.allocated_amount, money=True)
        write_cell(sheet, index, 4, item.currency)
    return workbook_bytes(workbook)


def _export_expiring(
    db: Session,
    current_user: CurrentUser,
    *,
    project_id: int | None,
    **_: object,
) -> bytes:
    repo = StatisticsRepository(db)
    today = business_today(db)
    days = get_expiring_days(db)
    items = repo.expiring_resources(current_user, days=days, project_id=project_id, today=today)
    workbook, sheet = new_export_workbook("expiring_resources")
    write_header(sheet, ["resource_name", "status", "expires_at", "days_remaining"])
    for index, item in enumerate(items, start=2):
        remaining = (item.expires_at - today).days if item.expires_at else None
        write_cell(sheet, index, 1, item.resource_name)
        write_cell(sheet, index, 2, item.status)
        write_cell(sheet, index, 3, item.expires_at, as_date=True)
        write_cell(sheet, index, 4, remaining)
    return workbook_bytes(workbook)


def _export_idle(
    db: Session,
    current_user: CurrentUser,
    *,
    project_id: int | None,
    **_: object,
) -> bytes:
    repo = StatisticsRepository(db)
    items = repo.idle_resources(current_user, project_id=project_id)
    workbook, sheet = new_export_workbook("idle_resources")
    write_header(sheet, ["resource_name", "status", "expires_at"])
    for index, item in enumerate(items, start=2):
        write_cell(sheet, index, 1, item.resource_name)
        write_cell(sheet, index, 2, item.status)
        write_cell(sheet, index, 3, item.expires_at, as_date=True)
    return workbook_bytes(workbook)


def _export_audit_logs(db: Session, current_user: CurrentUser, **_: object) -> bytes:
    workbook, sheet = new_export_workbook("audit_logs")
    write_header(sheet, ["created_at", "operator", "module", "action", "target_type", "target_id"])
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(5000).all()
    user_ids = {item.operator_user_id for item in logs if item.operator_user_id}
    users = {
        user.id: user.username
        for user in db.query(User).filter(User.id.in_(user_ids)).all()
    } if user_ids else {}
    for index, item in enumerate(logs, start=2):
        public_audit_payload(item)
        write_cell(sheet, index, 1, item.created_at.isoformat() if item.created_at else None)
        write_cell(sheet, index, 2, users.get(item.operator_user_id or 0))
        write_cell(sheet, index, 3, item.module)
        write_cell(sheet, index, 4, item.action)
        write_cell(sheet, index, 5, item.target_type)
        write_cell(sheet, index, 6, item.target_id)
    return workbook_bytes(workbook)
