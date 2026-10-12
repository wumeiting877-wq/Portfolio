from datetime import date

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query, Session, joinedload

from app.models.expense_distribution import ExpenseDistribution
from app.models.expense_record import ExpenseRecord
from app.models.expense_type import ExpenseType
from app.models.recurring_expense_rule import RecurringExpenseRule
from app.models.recurring_rule_distribution import RecurringRuleDistribution


class ExpenseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_type_by_id(self, type_id: int) -> ExpenseType | None:
        return self.db.query(ExpenseType).filter(ExpenseType.id == type_id).first()

    def get_type_by_code(self, code: str) -> ExpenseType | None:
        return self.db.query(ExpenseType).filter(ExpenseType.code == code).first()

    def add_type(self, expense_type: ExpenseType) -> ExpenseType:
        self.db.add(expense_type)
        self.db.flush()
        return expense_type

    def list_types(self, *, include_inactive: bool) -> list[ExpenseType]:
        query = self.db.query(ExpenseType)
        if not include_inactive:
            query = query.filter(ExpenseType.is_active.is_(True))
        return query.order_by(ExpenseType.id.asc()).all()

    def get_expense_by_id(self, expense_id: int) -> ExpenseRecord | None:
        return (
            self.db.query(ExpenseRecord)
            .options(
                joinedload(ExpenseRecord.expense_type),
                joinedload(ExpenseRecord.resource_account),
                joinedload(ExpenseRecord.distributions).joinedload(ExpenseDistribution.project),
                joinedload(ExpenseRecord.distributions).joinedload(ExpenseDistribution.employee),
            )
            .filter(ExpenseRecord.id == expense_id)
            .first()
        )

    def add_expense(self, expense: ExpenseRecord) -> ExpenseRecord:
        self.db.add(expense)
        self.db.flush()
        return expense

    def list_expenses_filtered(
        self,
        query: Query,
        *,
        keyword: str | None,
        expense_type_id: int | None,
        category: str | None,
        billing_mode: str | None,
        source: str | None,
        resource_account_id: int | None,
        project_id: int | None,
        employee_id: int | None,
        currency: str | None,
        date_from: date | None,
        date_to: date | None,
        billing_period: str | None,
        status: str | None,
    ) -> Query:
        query = query.options(
            joinedload(ExpenseRecord.expense_type),
            joinedload(ExpenseRecord.resource_account),
        )
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                or_(
                    ExpenseRecord.description.ilike(like),
                    ExpenseRecord.external_reference.ilike(like),
                    ExpenseType.name.ilike(like),
                    ExpenseType.code.ilike(like),
                )
            ).join(ExpenseType, ExpenseType.id == ExpenseRecord.expense_type_id)
        if expense_type_id:
            query = query.filter(ExpenseRecord.expense_type_id == expense_type_id)
        if category:
            type_ids = self.db.query(ExpenseType.id).filter(ExpenseType.category == category)
            query = query.filter(ExpenseRecord.expense_type_id.in_(type_ids))
        if billing_mode:
            query = query.filter(ExpenseRecord.billing_mode == billing_mode)
        if source:
            query = query.filter(ExpenseRecord.source == source)
        if resource_account_id:
            query = query.filter(ExpenseRecord.resource_account_id == resource_account_id)
        if currency:
            query = query.filter(ExpenseRecord.currency == currency)
        if date_from:
            query = query.filter(ExpenseRecord.expense_date >= date_from)
        if date_to:
            query = query.filter(ExpenseRecord.expense_date <= date_to)
        if billing_period:
            query = query.filter(
                or_(
                    ExpenseRecord.billing_period_start.cast(str).like(f"{billing_period}%"),
                    and_(
                        ExpenseRecord.billing_period_start.is_(None),
                        ExpenseRecord.expense_date.cast(str).like(f"{billing_period}%"),
                    ),
                )
            )
        if status:
            query = query.filter(ExpenseRecord.status == status)
        if project_id:
            matched = self.db.query(ExpenseDistribution.expense_record_id).filter(
                ExpenseDistribution.project_id == project_id
            )
            query = query.filter(ExpenseRecord.id.in_(matched))
        if employee_id:
            matched = self.db.query(ExpenseDistribution.expense_record_id).filter(
                ExpenseDistribution.employee_id == employee_id
            )
            query = query.filter(ExpenseRecord.id.in_(matched))
        return query

    def paginate(self, query: Query, *, page: int, page_size: int) -> tuple[list[ExpenseRecord], int]:
        total = query.order_by(None).count()
        items = (
            query.order_by(ExpenseRecord.expense_date.desc(), ExpenseRecord.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def get_recurring_by_id(self, rule_id: int) -> RecurringExpenseRule | None:
        return (
            self.db.query(RecurringExpenseRule)
            .options(
                joinedload(RecurringExpenseRule.expense_type),
                joinedload(RecurringExpenseRule.resource_account),
                joinedload(RecurringExpenseRule.distributions).joinedload(RecurringRuleDistribution.project),
                joinedload(RecurringExpenseRule.distributions).joinedload(RecurringRuleDistribution.employee),
            )
            .filter(RecurringExpenseRule.id == rule_id)
            .first()
        )

    def add_rule(self, rule: RecurringExpenseRule) -> RecurringExpenseRule:
        self.db.add(rule)
        self.db.flush()
        return rule

    def list_rules(self, *, include_inactive: bool) -> list[RecurringExpenseRule]:
        query = self.db.query(RecurringExpenseRule).options(
            joinedload(RecurringExpenseRule.expense_type),
            joinedload(RecurringExpenseRule.resource_account),
            joinedload(RecurringExpenseRule.distributions),
        )
        if not include_inactive:
            query = query.filter(RecurringExpenseRule.is_active.is_(True))
        return query.order_by(RecurringExpenseRule.id.desc()).all()

    def list_due_rules(self, as_of: date) -> list[RecurringExpenseRule]:
        return (
            self.db.query(RecurringExpenseRule)
            .options(
                joinedload(RecurringExpenseRule.expense_type),
                joinedload(RecurringExpenseRule.distributions),
            )
            .filter(
                RecurringExpenseRule.is_active.is_(True),
                RecurringExpenseRule.next_run_date <= as_of,
                RecurringExpenseRule.start_date <= as_of,
                or_(
                    RecurringExpenseRule.end_date.is_(None),
                    RecurringExpenseRule.end_date >= RecurringExpenseRule.next_run_date,
                ),
            )
            .order_by(RecurringExpenseRule.id.asc())
            .all()
        )

    def existing_generated(self, rule_id: int, billing_period_start: date) -> ExpenseRecord | None:
        return (
            self.db.query(ExpenseRecord)
            .filter(
                ExpenseRecord.recurring_rule_id == rule_id,
                ExpenseRecord.billing_period_start == billing_period_start,
            )
            .first()
        )
