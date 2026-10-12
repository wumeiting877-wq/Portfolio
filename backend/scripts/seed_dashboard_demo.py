"""Idempotent development-only data set for the frozen role dashboards.

Run from ``backend`` (or the backend container) with exactly one action:

    python scripts/seed_dashboard_demo.py --dry-run
    python scripts/seed_dashboard_demo.py --apply
    python scripts/seed_dashboard_demo.py --verify
    python scripts/seed_dashboard_demo.py --cleanup

The connection deliberately defaults to the published development PostgreSQL
endpoint (127.0.0.1:55432/project_cost_hub) instead of the compose-internal
endpoint.  Every mutating action is protected by strict environment guards.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from sqlalchemy import create_engine, func, or_
from sqlalchemy.orm import Session, joinedload, sessionmaker

# Allow ``python backend/scripts/seed_dashboard_demo.py`` as well as execution
# from the backend directory.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import Settings
from app.core.security import hash_password
from app.models.employee import Employee
from app.models.enums import (
    AllocationMethod,
    BillingMode,
    CurrencyCode,
    EmploymentStatus,
    ExpenseSource,
    ExpenseStatus,
    ProjectMemberRole,
    ProjectStatus,
    ResourceStatus,
    RoleCode,
    UserStatus,
)
from app.models.expense_distribution import ExpenseDistribution
from app.models.expense_record import ExpenseRecord
from app.models.expense_type import ExpenseType
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.resource_account import ResourceAccount
from app.models.resource_allocation import ResourceAllocation
from app.models.resource_type import ResourceType
from app.models.role import Role
from app.models.user import User
from app.permissions.dependencies import CurrentUser
from app.permissions.project_scope import readable_projects
from app.permissions.resource_scope import readable_resources
from app.services.settings_service import business_today, get_expiring_days
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


PREFIX = "DASH-DEMO-"
EXPECTED_ENV = "development"
EXPECTED_DB = "project_cost_hub"
EXPECTED_HOST = "127.0.0.1"
EXPECTED_PORT = 55432
DEMO_USERNAMES = (
    "demo_boss",
    "demo_pm_a",
    "demo_pm_b",
    "demo_member_a",
    "demo_member_b",
)


@dataclass(frozen=True)
class Target:
    app_env: str
    host: str
    port: int
    database: str
    user: str
    password: str
    connect_host: str
    connect_port: int

    @property
    def url(self) -> str:
        return (
            f"postgresql+psycopg://{quote_plus(self.user)}:{quote_plus(self.password)}"
            f"@{self.connect_host}:{self.connect_port}/{self.database}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--dry-run", action="store_true")
    actions.add_argument("--apply", action="store_true")
    actions.add_argument("--verify", action="store_true")
    actions.add_argument("--cleanup", action="store_true")
    parser.add_argument("--host", default=EXPECTED_HOST)
    parser.add_argument("--port", type=int, default=EXPECTED_PORT)
    parser.add_argument("--database", default=EXPECTED_DB)
    parser.add_argument(
        "--connect-host",
        default=None,
        help="transport override for container execution; does not change the guarded target",
    )
    parser.add_argument("--connect-port", type=int, default=None)
    return parser.parse_args()


def load_target(args: argparse.Namespace) -> Target:
    settings = Settings()
    return Target(
        app_env=(os.getenv("APP_ENV") or settings.APP_ENV).strip().lower(),
        host=args.host,
        port=args.port,
        database=args.database,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        connect_host=args.connect_host or args.host,
        connect_port=args.connect_port or args.port,
    )


def assert_safe_target(target: Target) -> None:
    failures: list[str] = []
    if target.app_env not in {"development", "dev"}:
        failures.append(f"APP_ENV must be development, got {target.app_env!r}")
    if target.host not in {"127.0.0.1", "localhost"}:
        failures.append(f"host must be local development PostgreSQL, got {target.host!r}")
    if target.port != EXPECTED_PORT:
        failures.append(f"port must be {EXPECTED_PORT}, got {target.port}")
    if target.database != EXPECTED_DB:
        failures.append(f"database must be {EXPECTED_DB!r}, got {target.database!r}")
    if "pilot" in target.database.lower():
        failures.append("pilot databases are forbidden")
    if failures:
        raise SystemExit("UNSAFE TARGET: " + "; ".join(failures))


def print_target(target: Target) -> None:
    print("TARGET ENVIRONMENT: DEVELOPMENT")
    print(f"TARGET DATABASE: {target.database}")
    print(f"TARGET POSTGRES PORT: {target.port}")
    print(f"TARGET POSTGRES HOST: {target.host}")
    print("PILOT TARGET: NO")


def month_start(value: date, offset: int = 0) -> date:
    index = value.year * 12 + value.month - 1 + offset
    return date(index // 12, index % 12 + 1, 1)


def month_end(value: date) -> date:
    return month_start(value, 1) - timedelta(days=1)


def current_user(user: User) -> CurrentUser:
    return CurrentUser(
        id=user.id,
        username=user.username,
        role=user.role.code,
        scope={
            RoleCode.BOSS.value: "GLOBAL",
            RoleCode.PROJECT_MANAGER.value: "MANAGED_PROJECTS",
            RoleCode.MEMBER.value: "MEMBER_PROJECTS",
        }[user.role.code],
        status=user.status,
        must_change_password=user.must_change_password,
        employee_id=user.employee_id,
        user=user,
    )


def upsert_by(db: Session, model: type, filters: dict[str, Any], values: dict[str, Any]):
    row = db.query(model).filter_by(**filters).first()
    if row is None:
        row = model(**filters, **values)
        db.add(row)
    else:
        for key, value in values.items():
            setattr(row, key, value)
    db.flush()
    return row


def ensure_employee(db: Session, number: str, name: str, department: str, position: str) -> Employee:
    return upsert_by(
        db,
        Employee,
        {"employee_no": number},
        {
            "name": name,
            "department": department,
            "position": position,
            "email": f"{number.lower()}@demo.invalid",
            "employment_status": EmploymentStatus.ACTIVE.value,
            "remark": f"{PREFIX} dashboard development fixture",
        },
    )


def ensure_user(db: Session, username: str, employee: Employee, role_code: str) -> User:
    role = db.query(Role).filter(Role.code == role_code).one()
    row = db.query(User).filter(User.username == username).first()
    password = os.getenv("DASHBOARD_DEMO_PASSWORD", "change_me")
    values = {
        "employee_id": employee.id,
        "role_id": role.id,
        "status": UserStatus.ACTIVE.value,
        "must_change_password": False,
    }
    if row is None:
        row = User(username=username, password_hash=hash_password(password), **values)
        db.add(row)
    else:
        for key, value in values.items():
            setattr(row, key, value)
    db.flush()
    return row


def ensure_member(db: Session, project: Project, employee: Employee, member_role: str) -> ProjectMember:
    return upsert_by(
        db,
        ProjectMember,
        {"project_id": project.id, "employee_id": employee.id},
        {
            "member_role": member_role,
            "is_active": True,
            "left_at": None,
        },
    )


def ensure_allocation(
    db: Session,
    resource: ResourceAccount,
    *,
    project: Project | None = None,
    employee: Employee | None = None,
) -> ResourceAllocation:
    assert project is not None or employee is not None
    if project is not None and employee is not None:
        is_member = (
            project.manager_employee_id == employee.id
            or db.query(ProjectMember)
            .filter_by(project_id=project.id, employee_id=employee.id, is_active=True)
            .first()
            is not None
        )
        if not is_member:
            raise RuntimeError(f"allocation target {employee.employee_no} is not in {project.project_code}")
    return upsert_by(
        db,
        ResourceAllocation,
        {
            "resource_account_id": resource.id,
            "project_id": project.id if project else None,
            "employee_id": employee.id if employee else None,
        },
        {
            "is_active": True,
            "released_at": None,
            "remark": f"{PREFIX} allocation",
        },
    )


def ensure_expense(
    db: Session,
    *,
    ref: str,
    expense_type: ExpenseType,
    resource: ResourceAccount | None,
    expense_date: date,
    amount: str,
    currency: str,
    billing_mode: str,
    distributions: list[tuple[Project | None, Employee | None, str]],
    created_by: int,
) -> ExpenseRecord:
    total = Decimal(amount)
    parts = [Decimal(item[2]) for item in distributions]
    if sum(parts, Decimal("0")) != total:
        raise RuntimeError(f"distribution total mismatch for {ref}")
    record = upsert_by(
        db,
        ExpenseRecord,
        {"external_reference": ref},
        {
            "expense_type_id": expense_type.id,
            "resource_account_id": resource.id if resource else None,
            "billing_mode": billing_mode,
            "source": ExpenseSource.MANUAL.value,
            "expense_date": expense_date,
            "billing_period_start": month_start(expense_date),
            "billing_period_end": month_end(expense_date),
            "amount": total,
            "currency": currency,
            "description": f"{PREFIX} dashboard fixture {ref}",
            "status": ExpenseStatus.ACTIVE.value,
            "created_by": created_by,
        },
    )
    db.query(ExpenseDistribution).filter_by(expense_record_id=record.id).delete(
        synchronize_session=False
    )
    for project, employee, allocated in distributions:
        db.add(
            ExpenseDistribution(
                expense_record_id=record.id,
                project_id=project.id if project else None,
                employee_id=employee.id if employee else None,
                allocation_method=AllocationMethod.DIRECT.value,
                allocated_amount=Decimal(allocated),
            )
        )
    db.flush()
    return record


def seed(db: Session) -> None:
    today = business_today(db)
    creator = db.query(User).filter(User.username == "admin").first()
    if creator is None:
        raise RuntimeError("admin bootstrap account is required before dashboard demo seeding")

    employees = {
        "boss": ensure_employee(db, f"{PREFIX}EMP-BOSS", "Demo 经营负责人", "管理层", "负责人"),
        "pm_a": ensure_employee(db, f"{PREFIX}EMP-PMA", "Demo PM-A", "研发中心", "项目经理"),
        "pm_b": ensure_employee(db, f"{PREFIX}EMP-PMB", "Demo PM-B", "交付中心", "项目经理"),
        "member_a": ensure_employee(db, f"{PREFIX}EMP-MA", "Demo Member-A", "研发中心", "研发工程师"),
        "member_b": ensure_employee(db, f"{PREFIX}EMP-MB", "Demo Member-B", "研发中心", "产品设计师"),
        "member_c": ensure_employee(db, f"{PREFIX}EMP-MC", "Demo Member-C", "平台中心", "运维工程师"),
    }
    users = {
        "boss": ensure_user(db, "demo_boss", employees["boss"], RoleCode.BOSS.value),
        "pm_a": ensure_user(db, "demo_pm_a", employees["pm_a"], RoleCode.PROJECT_MANAGER.value),
        "pm_b": ensure_user(db, "demo_pm_b", employees["pm_b"], RoleCode.PROJECT_MANAGER.value),
        "member_a": ensure_user(db, "demo_member_a", employees["member_a"], RoleCode.MEMBER.value),
        "member_b": ensure_user(db, "demo_member_b", employees["member_b"], RoleCode.MEMBER.value),
    }

    projects = {
        "a": upsert_by(
            db,
            Project,
            {"project_code": f"{PREFIX}PRJ-A"},
            {
                "name": "Demo Alpha",
                "description": f"{PREFIX} PM-A full dashboard project",
                "manager_employee_id": employees["pm_a"].id,
                "status": ProjectStatus.ACTIVE.value,
                "start_date": month_start(today, -8),
                "end_date": month_end(month_start(today, 4)),
                "created_by": creator.id,
            },
        ),
        "b": upsert_by(
            db,
            Project,
            {"project_code": f"{PREFIX}PRJ-B"},
            {
                "name": "企业协同 Demo Beta",
                "description": f"{PREFIX} PM-A empty-attention project",
                "manager_employee_id": employees["pm_a"].id,
                "status": ProjectStatus.PLANNING.value,
                "start_date": month_start(today, -3),
                "end_date": month_end(month_start(today, 6)),
                "created_by": creator.id,
            },
        ),
        "c": upsert_by(
            db,
            Project,
            {"project_code": f"{PREFIX}PRJ-C"},
            {
                "name": "资源费用验证 Demo Gamma",
                "description": f"{PREFIX} PM-B isolated project",
                "manager_employee_id": employees["pm_b"].id,
                "status": ProjectStatus.COMPLETED.value,
                "start_date": month_start(today, -10),
                "end_date": month_end(month_start(today, -1)),
                "created_by": creator.id,
            },
        ),
    }
    for key in ("pm_a", "member_a", "member_b", "member_c"):
        ensure_member(
            db,
            projects["a"],
            employees[key],
            ProjectMemberRole.PROJECT_MANAGER.value if key == "pm_a" else ProjectMemberRole.MEMBER.value,
        )
    for key in ("pm_a", "member_a"):
        ensure_member(
            db,
            projects["b"],
            employees[key],
            ProjectMemberRole.PROJECT_MANAGER.value if key == "pm_a" else ProjectMemberRole.MEMBER.value,
        )
    ensure_member(db, projects["c"], employees["pm_b"], ProjectMemberRole.PROJECT_MANAGER.value)

    resource_type_specs = {
        "ai": ("RT-AI", "AI / 大模型", "AI"),
        "dev": ("RT-DEV", "开发工具", "DEVELOPMENT"),
        "server": ("RT-SERVER", "服务器", "CLOUD_SERVER"),
        "saas": ("RT-SAAS", "SaaS", "SAAS"),
        "api": ("RT-API", "API", "API"),
    }
    resource_types = {
        key: upsert_by(
            db,
            ResourceType,
            {"code": f"{PREFIX}{code}"},
            {
                "name": f"{PREFIX}{name}",
                "category": category,
                "description": f"{PREFIX} dashboard resource type",
                "is_active": True,
            },
        )
        for key, (code, name, category) in resource_type_specs.items()
    }

    def resource(key: str, type_key: str, name: str, status: str, expires: date | None):
        return upsert_by(
            db,
            ResourceAccount,
            {"resource_name": f"{PREFIX}{name}"},
            {
                "resource_type_id": resource_types[type_key].id,
                "provider": "Dashboard Demo Provider",
                "account_identifier": f"{PREFIX}{key.upper()}",
                "plan_name": "Development Demo",
                "status": status,
                "purchased_at": month_start(today, -8),
                "activated_at": month_start(today, -7),
                "expires_at": expires,
                "remark": f"{PREFIX} dashboard resource",
                "created_by": creator.id,
            },
        )

    resources = {
        # Project A: expiring >=2, idle >=1, plus expired/disabled coverage.
        "a_gpt": resource("A-GPT", "ai", "GPT企业账号", ResourceStatus.ACTIVE.value, today + timedelta(days=10)),
        "a_api": resource("A-API", "api", "研发API共享额度", ResourceStatus.ACTIVE.value, today + timedelta(days=20)),
        "a_cloud": resource("A-CLOUD", "server", "Demo生产环境云服务器", ResourceStatus.ACTIVE.value, today + timedelta(days=180)),
        "a_idle": resource("A-IDLE", "dev", "Cursor研发团队账号", ResourceStatus.IDLE.value, today + timedelta(days=120)),
        "a_expired": resource("A-EXPIRED", "saas", "历史协作SaaS账号", ResourceStatus.EXPIRED.value, today - timedelta(days=5)),
        "a_disabled": resource("A-DISABLED", "dev", "停用开发工具账号", ResourceStatus.DISABLED.value, None),
        # Project B intentionally has no expiring, idle, or unassigned resources.
        "b_dev": resource("B-DEV", "dev", "Beta开发工具", ResourceStatus.ACTIVE.value, today + timedelta(days=180)),
        "b_saas": resource("B-SAAS", "saas", "Beta协同SaaS", ResourceStatus.ACTIVE.value, None),
        # Project C is isolated to PM-B.
        "c_server": resource("C-SERVER", "server", "Gamma归档服务器", ResourceStatus.ACTIVE.value, today + timedelta(days=240)),
        # Global-only unassigned ACTIVE resources for the BOSS attention column.
        "u_ai": resource("U-AI", "ai", "待分配AI试用账号", ResourceStatus.ACTIVE.value, today + timedelta(days=90)),
        "u_api": resource("U-API", "api", "待分配API套餐", ResourceStatus.ACTIVE.value, None),
    }

    ensure_allocation(db, resources["a_gpt"], project=projects["a"], employee=employees["member_a"])
    ensure_allocation(db, resources["a_api"], project=projects["a"], employee=employees["member_c"])
    ensure_allocation(db, resources["a_cloud"], project=projects["a"], employee=employees["member_a"])
    ensure_allocation(db, resources["a_idle"], project=projects["a"], employee=employees["member_a"])
    ensure_allocation(db, resources["a_expired"], project=projects["a"], employee=employees["member_b"])
    ensure_allocation(db, resources["a_disabled"], project=projects["a"], employee=employees["member_b"])
    ensure_allocation(db, resources["b_dev"], project=projects["b"], employee=employees["member_a"])
    ensure_allocation(db, resources["b_saas"], project=projects["b"])
    ensure_allocation(db, resources["c_server"], project=projects["c"], employee=employees["pm_b"])

    expense_type_specs = {
        "sub": ("EXP-SUB", "订阅费用", "SUBSCRIPTION"),
        "software": ("EXP-SOFTWARE", "软件费用", "SOFTWARE"),
        "server": ("EXP-SERVER", "服务器费用", "SERVER"),
        "api": ("EXP-API", "API 使用费", "API_USAGE"),
        "cloud": ("EXP-CLOUD", "云服务费", "CLOUD_SERVICE"),
    }
    expense_types = {
        key: upsert_by(
            db,
            ExpenseType,
            {"code": f"{PREFIX}{code}"},
            {
                "name": f"{PREFIX}{name}",
                "category": category,
                "description": f"{PREFIX} dashboard expense type",
                "is_active": True,
            },
        )
        for key, (code, name, category) in expense_type_specs.items()
    }

    cny_amounts = ["1900.00", "2600.00", "2200.00", "3500.00", "3100.00", "12800.00"]
    usd_amounts = {1: "20.00", 3: "80.00", 5: "100.00"}
    type_cycle = ["sub", "software", "server", "api", "cloud", "sub"]
    resource_cycle = ["a_gpt", "a_idle", "a_cloud", "a_api", "a_cloud", "a_gpt"]
    mode_cycle = [
        BillingMode.RECURRING.value,
        BillingMode.ONE_TIME.value,
        BillingMode.USAGE.value,
        BillingMode.MANUAL.value,
        BillingMode.RECURRING.value,
        BillingMode.USAGE.value,
    ]
    months = [month_start(today, offset) for offset in range(-5, 1)]
    for idx, period in enumerate(months):
        total = Decimal(cny_amounts[idx])
        member_a = (total * Decimal("0.50")).quantize(Decimal("0.01"))
        member_b = (total * Decimal("0.25")).quantize(Decimal("0.01"))
        public = total - member_a - member_b
        ensure_expense(
            db,
            ref=f"{PREFIX}EXP-A-{period:%Y%m}-CNY",
            expense_type=expense_types[type_cycle[idx]],
            resource=resources[resource_cycle[idx]],
            expense_date=period + timedelta(days=14),
            amount=str(total),
            currency=CurrencyCode.CNY.value,
            billing_mode=mode_cycle[idx],
            distributions=[
                (projects["a"], employees["member_a"], str(member_a)),
                (projects["a"], employees["member_b"], str(member_b)),
                (projects["a"], None, str(public)),
            ],
            created_by=creator.id,
        )
        if idx in usd_amounts:
            usd_total = Decimal(usd_amounts[idx])
            usd_member = (usd_total * Decimal("0.60")).quantize(Decimal("0.01"))
            ensure_expense(
                db,
                ref=f"{PREFIX}EXP-A-{period:%Y%m}-USD",
                expense_type=expense_types["api" if idx == 3 else "sub"],
                resource=resources["a_api" if idx == 3 else "a_gpt"],
                expense_date=period + timedelta(days=19),
                amount=str(usd_total),
                currency=CurrencyCode.USD.value,
                billing_mode=BillingMode.USAGE.value if idx == 3 else BillingMode.RECURRING.value,
                distributions=[
                    (projects["a"], employees["member_a"], str(usd_member)),
                    (projects["a"], None, str(usd_total - usd_member)),
                ],
                created_by=creator.id,
            )

        b_total = Decimal("99.00") + Decimal(idx * 50)
        ensure_expense(
            db,
            ref=f"{PREFIX}EXP-B-{period:%Y%m}-CNY",
            expense_type=expense_types["software" if idx % 2 == 0 else "sub"],
            resource=resources["b_dev" if idx % 2 == 0 else "b_saas"],
            expense_date=period + timedelta(days=9),
            amount=str(b_total),
            currency=CurrencyCode.CNY.value,
            billing_mode=BillingMode.RECURRING.value,
            distributions=[(projects["b"], employees["member_a"], str(b_total))],
            created_by=creator.id,
        )

    for idx, period in enumerate(months[-3:]):
        c_total = Decimal("1280.00") + Decimal(idx * 400)
        ensure_expense(
            db,
            ref=f"{PREFIX}EXP-C-{period:%Y%m}-CNY",
            expense_type=expense_types["server"],
            resource=resources["c_server"],
            expense_date=period + timedelta(days=11),
            amount=str(c_total),
            currency=CurrencyCode.CNY.value,
            billing_mode=BillingMode.MANUAL.value,
            distributions=[(projects["c"], employees["pm_b"], str(c_total))],
            created_by=creator.id,
        )

    db.commit()


def cleanup(db: Session) -> dict[str, int]:
    counts: dict[str, int] = {}
    expense_ids = [
        row[0]
        for row in db.query(ExpenseRecord.id)
        .filter(ExpenseRecord.external_reference.like(f"{PREFIX}%"))
        .all()
    ]
    counts["expense_distributions"] = (
        db.query(ExpenseDistribution)
        .filter(ExpenseDistribution.expense_record_id.in_(expense_ids))
        .delete(synchronize_session=False)
        if expense_ids
        else 0
    )
    counts["expense_records"] = (
        db.query(ExpenseRecord)
        .filter(ExpenseRecord.id.in_(expense_ids))
        .delete(synchronize_session=False)
        if expense_ids
        else 0
    )
    resource_ids = [
        row[0]
        for row in db.query(ResourceAccount.id)
        .filter(ResourceAccount.resource_name.like(f"{PREFIX}%"))
        .all()
    ]
    counts["resource_allocations"] = (
        db.query(ResourceAllocation)
        .filter(ResourceAllocation.resource_account_id.in_(resource_ids))
        .delete(synchronize_session=False)
        if resource_ids
        else 0
    )
    counts["resource_accounts"] = (
        db.query(ResourceAccount)
        .filter(ResourceAccount.id.in_(resource_ids))
        .delete(synchronize_session=False)
        if resource_ids
        else 0
    )
    project_ids = [
        row[0]
        for row in db.query(Project.id).filter(Project.project_code.like(f"{PREFIX}%")).all()
    ]
    counts["project_members"] = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id.in_(project_ids))
        .delete(synchronize_session=False)
        if project_ids
        else 0
    )
    counts["projects"] = (
        db.query(Project).filter(Project.id.in_(project_ids)).delete(synchronize_session=False)
        if project_ids
        else 0
    )
    employee_ids = [
        row[0]
        for row in db.query(Employee.id).filter(Employee.employee_no.like(f"{PREFIX}%")).all()
    ]
    counts["users"] = db.query(User).filter(
        or_(User.username.in_(DEMO_USERNAMES), User.employee_id.in_(employee_ids))
    ).delete(synchronize_session=False)
    counts["employees"] = (
        db.query(Employee).filter(Employee.id.in_(employee_ids)).delete(synchronize_session=False)
        if employee_ids
        else 0
    )
    counts["expense_types"] = db.query(ExpenseType).filter(
        ExpenseType.code.like(f"{PREFIX}%")
    ).delete(synchronize_session=False)
    counts["resource_types"] = db.query(ResourceType).filter(
        ResourceType.code.like(f"{PREFIX}%")
    ).delete(synchronize_session=False)
    db.commit()
    return counts


def _month_currency_map(series) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for item in series:
        result.setdefault(item.period, set()).add(item.currency)
    return result


def verify(db: Session) -> tuple[bool, list[tuple[str, bool, str]]]:
    today = business_today(db)
    start = month_start(today, -5)
    end = month_end(today)
    users = {
        row.username: row
        for row in db.query(User)
        .options(joinedload(User.role), joinedload(User.employee))
        .filter(User.username.in_(DEMO_USERNAMES))
        .all()
    }
    projects = {
        row.project_code: row
        for row in db.query(Project).filter(Project.project_code.like(f"{PREFIX}%")).all()
    }
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, condition: bool, detail: str) -> None:
        checks.append((name, bool(condition), detail))

    check("demo accounts", len(users) == 5, f"found={sorted(users)}")
    check("demo projects", len(projects) == 3, f"found={sorted(projects)}")
    if len(users) != 5 or len(projects) != 3:
        return False, checks

    boss = current_user(users["demo_boss"])
    pm_a = current_user(users["demo_pm_a"])
    pm_b = current_user(users["demo_pm_b"])
    member_a = current_user(users["demo_member_a"])
    member_b = current_user(users["demo_member_b"])
    project_a = projects[f"{PREFIX}PRJ-A"]
    project_b = projects[f"{PREFIX}PRJ-B"]
    project_c = projects[f"{PREFIX}PRJ-C"]

    boss_overview = get_overview(db, boss, date_from=start, date_to=end)
    boss_trend = get_expense_trend(db, boss, date_from=start, date_to=end)
    boss_status = get_resource_status(db, boss)
    boss_projects = get_project_costs(db, boss, date_from=start, date_to=end, limit=10)
    boss_types = get_resource_type_costs(
        db, boss, date_from=start, date_to=end, limit=10
    )
    boss_periods = _month_currency_map(boss_trend.series)
    check(
        "BOSS five KPI",
        bool(boss_overview.amounts_by_currency)
        and (boss_overview.project_count or 0) >= 3
        and (boss_overview.active_resource_count or 0) > 0
        and (boss_overview.idle_resource_count or 0) >= 1
        and (boss_overview.unassigned_active_resource_count or 0) >= 2
        and (boss_overview.expiring_soon_count or 0) >= 2,
        str(boss_overview.model_dump()),
    )
    check(
        "BOSS six-month currencies",
        len(boss_periods) == 6
        and all("CNY" in currencies for currencies in boss_periods.values())
        and sum("USD" in currencies for currencies in boss_periods.values()) >= 3,
        str({key: sorted(value) for key, value in boss_periods.items()}),
    )
    check("BOSS project costs", len({x.project_id for x in boss_projects.items}) >= 3, f"items={len(boss_projects.items)}")
    check("BOSS cost structure", len({x.resource_type_code for x in boss_types.items}) >= 3, f"types={len(boss_types.items)}")
    check(
        "BOSS all resource statuses",
        all(boss_status.counts.get(key, 0) >= 1 for key in ("ACTIVE", "IDLE", "EXPIRED", "DISABLED", "EXPIRING_SOON", "UNASSIGNED_ACTIVE")),
        str(boss_status.counts),
    )
    check(
        "BOSS attention",
        len(get_expiring_resources(db, boss, days=get_expiring_days(db)).items) >= 2
        and boss_status.unassigned_active_count >= 2
        and boss_status.explicit_idle_count >= 1,
        f"expiring={len(get_expiring_resources(db, boss, days=get_expiring_days(db)).items)} unassigned={boss_status.unassigned_active_count} idle={boss_status.explicit_idle_count}",
    )

    pm_a_projects = readable_projects(db, pm_a).all()
    pm_b_projects = readable_projects(db, pm_b).all()
    check("PM-A managed projects", {x.id for x in pm_a_projects} == {project_a.id, project_b.id}, str([x.project_code for x in pm_a_projects]))
    check("PM-B isolation", {x.id for x in pm_b_projects} == {project_c.id}, str([x.project_code for x in pm_b_projects]))

    a_overview = get_overview(db, pm_a, date_from=start, date_to=end, project_id=project_a.id)
    a_trend = get_expense_trend(db, pm_a, date_from=start, date_to=end, project_id=project_a.id)
    a_status = get_resource_status(db, pm_a, project_id=project_a.id)
    a_employee = get_employee_costs(db, pm_a, date_from=start, date_to=end, project_id=project_a.id, limit=10)
    a_types = get_resource_type_costs(db, pm_a, date_from=start, date_to=end, project_id=project_a.id, limit=10)
    check(
        "PM-A Project A modules",
        bool(a_overview.amounts_by_currency)
        and len(a_trend.series) >= 6
        and len(a_employee.items) >= 2
        and len(a_employee.project_public_costs) >= 1
        and len(a_types.items) >= 3
        and a_status.explicit_idle_count >= 1
        and len(get_expiring_resources(db, pm_a, days=get_expiring_days(db), project_id=project_a.id).items) >= 2,
        f"overview={a_overview.model_dump()} status={a_status.counts}",
    )
    # Frozen service semantics make this impossible: project-scoped resources
    # require an active allocation while UNASSIGNED_ACTIVE forbids one.
    check(
        "DEMO DATA GAP: Project A unassigned resource",
        a_status.unassigned_active_count >= 1,
        "frozen statistics query requires active project allocation and zero active allocations simultaneously",
    )
    b_status = get_resource_status(db, pm_a, project_id=project_b.id)
    b_expiring = get_expiring_resources(db, pm_a, days=get_expiring_days(db), project_id=project_b.id)
    check(
        "PM-A Project B empty attention",
        b_status.explicit_idle_count == 0
        and b_status.unassigned_active_count == 0
        and len(b_expiring.items) == 0,
        f"status={b_status.counts} expiring={len(b_expiring.items)}",
    )

    ma_overview = get_overview(db, member_a, date_from=start, date_to=end, employee_id=member_a.employee_id)
    ma_trend = get_expense_trend(db, member_a, date_from=start, date_to=end, employee_id=member_a.employee_id)
    ma_types = get_resource_type_costs(db, member_a, date_from=start, date_to=end, employee_id=member_a.employee_id, limit=10)
    ma_resources = readable_resources(db, member_a).all()
    ma_periods = _month_currency_map(ma_trend.series)
    check(
        "Member-A full coverage",
        (ma_overview.my_project_count or 0) >= 2
        and len(ma_resources) >= 3
        and len({x.resource_type_id for x in ma_resources}) >= 2
        and len(ma_periods) == 6
        and all("CNY" in value for value in ma_periods.values())
        and any("USD" in value for value in ma_periods.values())
        and len(ma_types.items) >= 2
        and (ma_overview.my_expiring_resource_count or 0) >= 1,
        f"overview={ma_overview.model_dump()} resources={len(ma_resources)} periods={ma_periods}",
    )
    mb_overview = get_overview(db, member_b, date_from=start, date_to=end, employee_id=member_b.employee_id)
    check("Member-B empty expiring", (mb_overview.my_expiring_resource_count or 0) == 0, str(mb_overview.model_dump()))

    ma_resource_ids = {x.id for x in readable_resources(db, member_a).all()}
    mb_resource_ids = {x.id for x in readable_resources(db, member_b).all()}
    ma_amounts = get_overview(db, member_a, date_from=start, date_to=end, employee_id=member_a.employee_id).amounts_by_currency
    mb_amounts = get_overview(db, member_b, date_from=start, date_to=end, employee_id=member_b.employee_id).amounts_by_currency
    check(
        "cross-member direct resource isolation",
        ma_resource_ids.isdisjoint(mb_resource_ids),
        f"member_a={sorted(ma_resource_ids)} member_b={sorted(mb_resource_ids)}",
    )
    check(
        "cross-member direct expense isolation",
        ma_amounts != mb_amounts and bool(ma_amounts) and bool(mb_amounts),
        f"member_a={ma_amounts} member_b={mb_amounts}",
    )

    billing = get_billing_costs(db, boss, date_from=start, date_to=end)
    check(
        "billing modes",
        {x.billing_mode for x in billing.items}
        >= {"RECURRING", "ONE_TIME", "USAGE", "MANUAL"},
        str(sorted({x.billing_mode for x in billing.items})),
    )
    return all(item[1] for item in checks), checks


def print_plan() -> None:
    print("ACTION: DRY RUN (no database connection, no writes)")
    print("PLAN: upsert 6 employees, 5 accounts, 3 projects, 5 resource types, 11 resources")
    print("PLAN: upsert 5 expense types and dynamic six-month CNY/USD expenses")
    print("PLAN: preserve all non-DASH-DEMO data; Pilot is not addressed")
    print("KNOWN DEMO DATA GAP: project-scoped UNASSIGNED_ACTIVE is impossible under frozen statistics semantics")


def main() -> int:
    args = parse_args()
    target = load_target(args)
    assert_safe_target(target)
    print_target(target)
    if args.dry_run:
        print_plan()
        return 0

    engine = create_engine(target.url, pool_pre_ping=True, future=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
    with session_factory() as db:
        actual_db = db.query(func.current_database()).scalar()
        if actual_db != EXPECTED_DB:
            raise SystemExit(f"connected database mismatch: {actual_db!r}")
        if args.apply:
            seed(db)
            print("APPLY: COMPLETE")
            return 0
        if args.cleanup:
            counts = cleanup(db)
            print(f"CLEANUP: COMPLETE {counts}")
            return 0
        passed, checks = verify(db)
        for name, ok, detail in checks:
            print(f"{'PASS' if ok else 'FAIL'} | {name} | {detail}")
        print(f"DASHBOARD FULL DEMO DATA: {'PASS' if passed else 'FAIL'}")
        return 0 if passed else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
