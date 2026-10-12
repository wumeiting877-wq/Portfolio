from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Query, Session, joinedload

from app.core.money import quantize_money
from app.models.employee import Employee
from app.models.enums import ExpenseStatus, ResourceStatus
from app.models.expense_distribution import ExpenseDistribution
from app.models.expense_record import ExpenseRecord
from app.models.expense_type import ExpenseType
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.resource_account import ResourceAccount
from app.models.resource_allocation import ResourceAllocation
from app.models.resource_type import ResourceType
from app.permissions.dependencies import CurrentUser
from app.permissions.expense_scope import readable_distributions
from app.permissions.project_scope import readable_projects
from app.permissions.resource_scope import readable_resources
from app.repositories.resource_repository import EXPIRING_SOON_DAYS

UNBOUND_CODE = "UNBOUND"
UNBOUND_NAME = "未关联资源"


def _money_map(rows: list[tuple[str, Decimal | None]]) -> dict[str, str]:
    amounts: dict[str, str] = {}
    for currency, total in sorted(rows, key=lambda item: item[0] or ""):
        if not currency:
            continue
        amounts[currency] = format(quantize_money(total or Decimal("0")), "f")
    return amounts


def _limit_per_currency(rows: list, *, currency_index: int, limit: int) -> list:
    seen: dict[str, int] = {}
    limited: list = []
    for row in rows:
        currency = row[currency_index]
        seen[currency] = seen.get(currency, 0) + 1
        if seen[currency] <= limit:
            limited.append(row)
    return limited


class StatisticsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def visible_active_distributions(
        self,
        current_user: CurrentUser,
        *,
        date_from: date | None,
        date_to: date | None,
        project_id: int | None = None,
        employee_id: int | None = None,
    ) -> Query:
        query = readable_distributions(self.db, current_user).join(
            ExpenseRecord, ExpenseRecord.id == ExpenseDistribution.expense_record_id
        )
        query = query.filter(ExpenseRecord.status == ExpenseStatus.ACTIVE.value)
        if date_from is not None:
            query = query.filter(ExpenseRecord.expense_date >= date_from)
        if date_to is not None:
            query = query.filter(ExpenseRecord.expense_date <= date_to)
        if project_id is not None:
            query = query.filter(ExpenseDistribution.project_id == project_id)
        if employee_id is not None:
            query = query.filter(ExpenseDistribution.employee_id == employee_id)
        return query

    def amounts_by_currency(
        self,
        current_user: CurrentUser,
        *,
        date_from: date | None,
        date_to: date | None,
        project_id: int | None = None,
        employee_id: int | None = None,
    ) -> dict[str, str]:
        rows = (
            self.visible_active_distributions(
                current_user,
                date_from=date_from,
                date_to=date_to,
                project_id=project_id,
                employee_id=employee_id,
            )
            .with_entities(
                ExpenseRecord.currency,
                func.sum(ExpenseDistribution.allocated_amount),
            )
            .group_by(ExpenseRecord.currency)
            .all()
        )
        return _money_map(rows)

    def expense_trend(
        self,
        current_user: CurrentUser,
        *,
        date_from: date | None,
        date_to: date | None,
        project_id: int | None = None,
        employee_id: int | None = None,
    ) -> list[tuple[str, str, Decimal]]:
        period = func.to_char(ExpenseRecord.expense_date, "YYYY-MM")
        rows = (
            self.visible_active_distributions(
                current_user,
                date_from=date_from,
                date_to=date_to,
                project_id=project_id,
                employee_id=employee_id,
            )
            .with_entities(
                period,
                ExpenseRecord.currency,
                func.sum(ExpenseDistribution.allocated_amount),
            )
            .group_by(period, ExpenseRecord.currency)
            .order_by(period.asc(), ExpenseRecord.currency.asc())
            .all()
        )
        return [(row[0], row[1], quantize_money(row[2] or Decimal("0"))) for row in rows]

    def project_costs(
        self,
        current_user: CurrentUser,
        *,
        date_from: date | None,
        date_to: date | None,
        project_id: int | None = None,
        limit: int,
    ) -> list[tuple[int, str, str, Decimal]]:
        rows = (
            self.visible_active_distributions(
                current_user,
                date_from=date_from,
                date_to=date_to,
                project_id=project_id,
            )
            .join(Project, Project.id == ExpenseDistribution.project_id)
            .filter(ExpenseDistribution.project_id.isnot(None))
            .with_entities(
                ExpenseDistribution.project_id,
                Project.name,
                ExpenseRecord.currency,
                func.sum(ExpenseDistribution.allocated_amount),
            )
            .group_by(ExpenseDistribution.project_id, Project.name, ExpenseRecord.currency)
            .order_by(func.sum(ExpenseDistribution.allocated_amount).desc())
            .all()
        )
        limited = _limit_per_currency(rows, currency_index=2, limit=limit)
        return [
            (row[0], row[1], row[2], quantize_money(row[3] or Decimal("0")))
            for row in limited
        ]

    def employee_costs(
        self,
        current_user: CurrentUser,
        *,
        date_from: date | None,
        date_to: date | None,
        project_id: int | None = None,
        employee_id: int | None = None,
        limit: int,
    ) -> list[tuple[int, str, str | None, str, Decimal]]:
        rows = (
            self.visible_active_distributions(
                current_user,
                date_from=date_from,
                date_to=date_to,
                project_id=project_id,
                employee_id=employee_id,
            )
            .join(Employee, Employee.id == ExpenseDistribution.employee_id)
            .filter(ExpenseDistribution.employee_id.isnot(None))
            .with_entities(
                ExpenseDistribution.employee_id,
                Employee.name,
                Employee.employee_no,
                ExpenseRecord.currency,
                func.sum(ExpenseDistribution.allocated_amount),
            )
            .group_by(
                ExpenseDistribution.employee_id,
                Employee.name,
                Employee.employee_no,
                ExpenseRecord.currency,
            )
            .order_by(func.sum(ExpenseDistribution.allocated_amount).desc())
            .all()
        )
        limited = _limit_per_currency(rows, currency_index=3, limit=limit)
        return [
            (row[0], row[1], row[2], row[3], quantize_money(row[4] or Decimal("0")))
            for row in limited
        ]

    def project_public_costs(
        self,
        current_user: CurrentUser,
        *,
        date_from: date | None,
        date_to: date | None,
        project_id: int | None = None,
        limit: int,
    ) -> list[tuple[int, str, str, Decimal]]:
        rows = (
            self.visible_active_distributions(
                current_user,
                date_from=date_from,
                date_to=date_to,
                project_id=project_id,
            )
            .join(Project, Project.id == ExpenseDistribution.project_id)
            .filter(
                ExpenseDistribution.project_id.isnot(None),
                ExpenseDistribution.employee_id.is_(None),
            )
            .with_entities(
                ExpenseDistribution.project_id,
                Project.name,
                ExpenseRecord.currency,
                func.sum(ExpenseDistribution.allocated_amount),
            )
            .group_by(ExpenseDistribution.project_id, Project.name, ExpenseRecord.currency)
            .order_by(func.sum(ExpenseDistribution.allocated_amount).desc())
            .all()
        )
        limited = _limit_per_currency(rows, currency_index=2, limit=limit)
        return [
            (row[0], row[1], row[2], quantize_money(row[3] or Decimal("0")))
            for row in limited
        ]

    def resource_type_costs(
        self,
        current_user: CurrentUser,
        *,
        date_from: date | None,
        date_to: date | None,
        project_id: int | None = None,
        employee_id: int | None = None,
        limit: int,
    ) -> list[tuple[int | None, str, str, str, Decimal]]:
        rows = (
            self.visible_active_distributions(
                current_user,
                date_from=date_from,
                date_to=date_to,
                project_id=project_id,
                employee_id=employee_id,
            )
            .outerjoin(ResourceAccount, ResourceAccount.id == ExpenseRecord.resource_account_id)
            .outerjoin(ResourceType, ResourceType.id == ResourceAccount.resource_type_id)
            .with_entities(
                ResourceType.id,
                func.coalesce(ResourceType.code, UNBOUND_CODE),
                func.coalesce(ResourceType.name, UNBOUND_NAME),
                ExpenseRecord.currency,
                func.sum(ExpenseDistribution.allocated_amount),
            )
            .group_by(
                ResourceType.id,
                func.coalesce(ResourceType.code, UNBOUND_CODE),
                func.coalesce(ResourceType.name, UNBOUND_NAME),
                ExpenseRecord.currency,
            )
            .order_by(func.sum(ExpenseDistribution.allocated_amount).desc())
            .all()
        )
        limited = _limit_per_currency(rows, currency_index=3, limit=limit)
        return [
            (row[0], row[1], row[2], row[3], quantize_money(row[4] or Decimal("0")))
            for row in limited
        ]

    def billing_costs(
        self,
        current_user: CurrentUser,
        *,
        date_from: date | None,
        date_to: date | None,
        project_id: int | None = None,
        employee_id: int | None = None,
    ) -> list[tuple[str, str, str, Decimal]]:
        rows = (
            self.visible_active_distributions(
                current_user,
                date_from=date_from,
                date_to=date_to,
                project_id=project_id,
                employee_id=employee_id,
            )
            .join(ExpenseType, ExpenseType.id == ExpenseRecord.expense_type_id)
            .with_entities(
                ExpenseRecord.billing_mode,
                ExpenseType.category,
                ExpenseRecord.currency,
                func.sum(ExpenseDistribution.allocated_amount),
            )
            .group_by(ExpenseRecord.billing_mode, ExpenseType.category, ExpenseRecord.currency)
            .order_by(ExpenseRecord.billing_mode.asc(), ExpenseType.category.asc(), ExpenseRecord.currency.asc())
            .all()
        )
        return [
            (row[0], row[1], row[2], quantize_money(row[3] or Decimal("0")))
            for row in rows
        ]

    def _scoped_resources(
        self,
        current_user: CurrentUser,
        *,
        project_id: int | None = None,
    ) -> Query:
        query = readable_resources(self.db, current_user)
        if project_id is not None:
            allocated = self.db.query(ResourceAllocation.resource_account_id).filter(
                ResourceAllocation.is_active.is_(True),
                ResourceAllocation.project_id == project_id,
            )
            query = query.filter(ResourceAccount.id.in_(allocated))
        return query

    def _active_allocation_subquery(self):
        return (
            self.db.query(
                ResourceAllocation.resource_account_id.label("rid"),
                func.count(ResourceAllocation.id).label("cnt"),
            )
            .filter(ResourceAllocation.is_active.is_(True))
            .group_by(ResourceAllocation.resource_account_id)
            .subquery()
        )

    def resource_status_counts(
        self,
        current_user: CurrentUser,
        *,
        project_id: int | None = None,
        days: int = EXPIRING_SOON_DAYS,
        today: date | None = None,
    ) -> dict[str, int]:
        today = today or date.today()
        alloc = self._active_allocation_subquery()
        query = self._scoped_resources(current_user, project_id=project_id).outerjoin(
            alloc, ResourceAccount.id == alloc.c.rid
        )
        unassigned = and_(
            ResourceAccount.status == ResourceStatus.ACTIVE.value,
            or_(alloc.c.cnt.is_(None), alloc.c.cnt == 0),
        )
        expiring = and_(
            ResourceAccount.expires_at > today,
            ResourceAccount.expires_at <= today + timedelta(days=days),
        )
        row = query.with_entities(
            func.count(ResourceAccount.id),
            func.coalesce(
                func.sum(case((ResourceAccount.status == ResourceStatus.ACTIVE.value, 1), else_=0)),
                0,
            ),
            func.coalesce(
                func.sum(case((ResourceAccount.status == ResourceStatus.IDLE.value, 1), else_=0)),
                0,
            ),
            func.coalesce(
                func.sum(case((ResourceAccount.status == ResourceStatus.EXPIRED.value, 1), else_=0)),
                0,
            ),
            func.coalesce(
                func.sum(case((ResourceAccount.status == ResourceStatus.DISABLED.value, 1), else_=0)),
                0,
            ),
            func.coalesce(func.sum(case((expiring, 1), else_=0)), 0),
            func.coalesce(func.sum(case((unassigned, 1), else_=0)), 0),
        ).one()
        return {
            "total": int(row[0] or 0),
            ResourceStatus.ACTIVE.value: int(row[1] or 0),
            ResourceStatus.IDLE.value: int(row[2] or 0),
            ResourceStatus.EXPIRED.value: int(row[3] or 0),
            ResourceStatus.DISABLED.value: int(row[4] or 0),
            "EXPIRING_SOON": int(row[5] or 0),
            "UNASSIGNED_ACTIVE": int(row[6] or 0),
        }

    def idle_resources(
        self,
        current_user: CurrentUser,
        *,
        project_id: int | None = None,
        limit: int = 20,
    ) -> list[ResourceAccount]:
        return (
            self._scoped_resources(current_user, project_id=project_id)
            .options(joinedload(ResourceAccount.resource_type))
            .filter(ResourceAccount.status == ResourceStatus.IDLE.value)
            .order_by(ResourceAccount.id.desc())
            .limit(limit)
            .all()
        )

    def unassigned_active_resources(
        self,
        current_user: CurrentUser,
        *,
        project_id: int | None = None,
        limit: int = 20,
    ) -> list[ResourceAccount]:
        alloc = self._active_allocation_subquery()
        return (
            self._scoped_resources(current_user, project_id=project_id)
            .options(joinedload(ResourceAccount.resource_type))
            .outerjoin(alloc, ResourceAccount.id == alloc.c.rid)
            .filter(
                ResourceAccount.status == ResourceStatus.ACTIVE.value,
                or_(alloc.c.cnt.is_(None), alloc.c.cnt == 0),
            )
            .order_by(ResourceAccount.id.desc())
            .limit(limit)
            .all()
        )

    def expiring_resources(
        self,
        current_user: CurrentUser,
        *,
        days: int,
        project_id: int | None = None,
        today: date | None = None,
        limit: int = 100,
    ) -> list[ResourceAccount]:
        today = today or date.today()
        return (
            self._scoped_resources(current_user, project_id=project_id)
            .options(joinedload(ResourceAccount.resource_type))
            .filter(
                ResourceAccount.expires_at > today,
                ResourceAccount.expires_at <= today + timedelta(days=days),
            )
            .order_by(ResourceAccount.expires_at.asc(), ResourceAccount.id.asc())
            .limit(limit)
            .all()
        )

    def project_count(self, current_user: CurrentUser, *, project_id: int | None = None) -> int:
        query = readable_projects(self.db, current_user)
        if project_id is not None:
            query = query.filter(Project.id == project_id)
        return int(query.with_entities(func.count(Project.id)).scalar() or 0)

    def employee_count(self, current_user: CurrentUser, *, project_id: int | None = None) -> int:
        from app.permissions.expense_scope import is_global_expense_reader

        if is_global_expense_reader(current_user) and project_id is None:
            return int(self.db.query(func.count(Employee.id)).scalar() or 0)

        projects = readable_projects(self.db, current_user)
        if project_id is not None:
            projects = projects.filter(Project.id == project_id)
        project_ids = projects.with_entities(Project.id)
        members = self.db.query(ProjectMember.employee_id.label("eid")).filter(
            ProjectMember.project_id.in_(project_ids),
            ProjectMember.is_active.is_(True),
        )
        managers = projects.with_entities(Project.manager_employee_id.label("eid"))
        combined = members.union(managers).subquery()
        return int(self.db.query(func.count()).select_from(combined).scalar() or 0)

    def resource_count(self, current_user: CurrentUser, *, project_id: int | None = None) -> int:
        return int(
            self._scoped_resources(current_user, project_id=project_id)
            .with_entities(func.count(ResourceAccount.id))
            .scalar()
            or 0
        )
