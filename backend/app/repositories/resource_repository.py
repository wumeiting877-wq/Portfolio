from datetime import date, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Query, Session, joinedload

from app.models.resource_account import ResourceAccount
from app.models.resource_allocation import ResourceAllocation
from app.models.resource_type import ResourceType

EXPIRING_SOON_DAYS = 30


class ResourceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_type_by_id(self, type_id: int) -> ResourceType | None:
        return self.db.query(ResourceType).filter(ResourceType.id == type_id).first()

    def get_type_by_code(self, code: str) -> ResourceType | None:
        return self.db.query(ResourceType).filter(ResourceType.code == code).first()

    def count_accounts_for_type(self, type_id: int) -> int:
        total = (
            self.db.query(func.count(ResourceAccount.id))
            .filter(ResourceAccount.resource_type_id == type_id)
            .scalar()
        )
        return int(total or 0)

    def add_type(self, resource_type: ResourceType) -> ResourceType:
        self.db.add(resource_type)
        self.db.flush()
        return resource_type

    def list_types(self, *, include_inactive: bool) -> list[ResourceType]:
        query = self.db.query(ResourceType)
        if not include_inactive:
            query = query.filter(ResourceType.is_active.is_(True))
        return query.order_by(ResourceType.id.asc()).all()

    def get_account_by_name(self, resource_name: str) -> ResourceAccount | None:
        return (
            self.db.query(ResourceAccount)
            .filter(ResourceAccount.resource_name == resource_name)
            .first()
        )

    def get_account_by_id(self, resource_id: int) -> ResourceAccount | None:
        return (
            self.db.query(ResourceAccount)
            .options(joinedload(ResourceAccount.resource_type))
            .filter(ResourceAccount.id == resource_id)
            .first()
        )

    def add_account(self, account: ResourceAccount) -> ResourceAccount:
        self.db.add(account)
        self.db.flush()
        return account

    def list_accounts_filtered(
        self,
        query: Query,
        *,
        keyword: str | None,
        resource_type_id: int | None,
        category: str | None,
        status: str | None,
        project_id: int | None,
        employee_id: int | None,
        expiring_soon: bool,
        today: date | None = None,
        days: int | None = None,
    ) -> Query:
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                or_(
                    ResourceAccount.resource_name.ilike(like),
                    ResourceAccount.provider.ilike(like),
                    ResourceAccount.account_identifier.ilike(like),
                    ResourceAccount.plan_name.ilike(like),
                )
            )
        if resource_type_id:
            query = query.filter(ResourceAccount.resource_type_id == resource_type_id)
        if category:
            type_ids = self.db.query(ResourceType.id).filter(ResourceType.category == category)
            query = query.filter(ResourceAccount.resource_type_id.in_(type_ids))
        if status:
            query = query.filter(ResourceAccount.status == status)
        if project_id:
            allocated = self.db.query(ResourceAllocation.resource_account_id).filter(
                ResourceAllocation.is_active.is_(True),
                ResourceAllocation.project_id == project_id,
            )
            query = query.filter(ResourceAccount.id.in_(allocated))
        if employee_id:
            allocated = self.db.query(ResourceAllocation.resource_account_id).filter(
                ResourceAllocation.is_active.is_(True),
                ResourceAllocation.employee_id == employee_id,
            )
            query = query.filter(ResourceAccount.id.in_(allocated))
        if expiring_soon:
            today = today or date.today()
            horizon = days if days is not None else EXPIRING_SOON_DAYS
            query = query.filter(
                ResourceAccount.expires_at > today,
                ResourceAccount.expires_at <= today + timedelta(days=horizon),
            )
        return query

    def paginate_accounts(
        self, query: Query, *, page: int, page_size: int
    ) -> tuple[list[ResourceAccount], int]:
        total = query.order_by(None).count()
        items = (
            query.options(joinedload(ResourceAccount.resource_type))
            .order_by(ResourceAccount.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def get_allocation_by_id(self, allocation_id: int) -> ResourceAllocation | None:
        return (
            self.db.query(ResourceAllocation)
            .options(
                joinedload(ResourceAllocation.project),
                joinedload(ResourceAllocation.employee),
            )
            .filter(ResourceAllocation.id == allocation_id)
            .first()
        )

    def find_allocation(
        self,
        resource_id: int,
        project_id: int | None,
        employee_id: int | None,
    ) -> ResourceAllocation | None:
        query = self.db.query(ResourceAllocation).filter(
            ResourceAllocation.resource_account_id == resource_id,
        )
        if project_id is None:
            query = query.filter(ResourceAllocation.project_id.is_(None))
        else:
            query = query.filter(ResourceAllocation.project_id == project_id)
        if employee_id is None:
            query = query.filter(ResourceAllocation.employee_id.is_(None))
        else:
            query = query.filter(ResourceAllocation.employee_id == employee_id)
        return query.first()

    def add_allocation(self, allocation: ResourceAllocation) -> ResourceAllocation:
        self.db.add(allocation)
        self.db.flush()
        return allocation

    def paginate_allocations(
        self, query: Query, *, page: int, page_size: int
    ) -> tuple[list[ResourceAllocation], int]:
        total = query.order_by(None).count()
        items = (
            query.options(
                joinedload(ResourceAllocation.project),
                joinedload(ResourceAllocation.employee),
            )
            .order_by(ResourceAllocation.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def list_allocations(self, query: Query) -> list[ResourceAllocation]:
        return (
            query.options(
                joinedload(ResourceAllocation.project),
                joinedload(ResourceAllocation.employee),
            )
            .order_by(ResourceAllocation.id.desc())
            .all()
        )

    def active_allocation_stats(self, resource_ids: list[int]) -> dict[int, dict[str, int]]:
        if not resource_ids:
            return {}
        rows = (
            self.db.query(
                ResourceAllocation.resource_account_id,
                func.count(ResourceAllocation.id),
                func.count(func.distinct(ResourceAllocation.employee_id)),
                func.count(func.distinct(ResourceAllocation.project_id)),
            )
            .filter(
                ResourceAllocation.resource_account_id.in_(resource_ids),
                ResourceAllocation.is_active.is_(True),
            )
            .group_by(ResourceAllocation.resource_account_id)
            .all()
        )
        return {
            resource_id: {
                "active_count": active_count,
                "active_user_count": user_count,
                "active_project_count": project_count,
            }
            for resource_id, active_count, user_count, project_count in rows
        }

    def usage_projects_by_resource(
        self, query: Query, resource_ids: list[int]
    ) -> dict[int, list[tuple[int, str, str]]]:
        if not resource_ids:
            return {}
        rows = (
            query.filter(
                ResourceAllocation.resource_account_id.in_(resource_ids),
                ResourceAllocation.is_active.is_(True),
                ResourceAllocation.project_id.is_not(None),
            )
            .options(joinedload(ResourceAllocation.project))
            .all()
        )
        grouped: dict[int, list[tuple[int, str, str]]] = {}
        seen: dict[int, set[int]] = {}
        for allocation in rows:
            project = allocation.project
            if project is None:
                continue
            resource_id = allocation.resource_account_id
            used = seen.setdefault(resource_id, set())
            if project.id in used:
                continue
            used.add(project.id)
            grouped.setdefault(resource_id, []).append(
                (project.id, project.name, project.project_code)
            )
        return grouped
