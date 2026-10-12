from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import BillingMode, ExpenseSource, ExpenseStatus

if TYPE_CHECKING:
    from app.models.expense_distribution import ExpenseDistribution
    from app.models.expense_type import ExpenseType
    from app.models.recurring_expense_rule import RecurringExpenseRule
    from app.models.resource_account import ResourceAccount


class ExpenseRecord(Base):
    __tablename__ = "expense_records"
    __table_args__ = (
        Index(
            "uq_expense_records_recurring_period",
            "recurring_rule_id",
            "billing_period_start",
            unique=True,
            postgresql_where=text(
                "recurring_rule_id IS NOT NULL AND billing_period_start IS NOT NULL"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    expense_type_id: Mapped[int] = mapped_column(ForeignKey("expense_types.id"), nullable=False, index=True)
    resource_account_id: Mapped[int | None] = mapped_column(
        ForeignKey("resource_accounts.id"), nullable=True, index=True
    )
    billing_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default=BillingMode.MANUAL.value, index=True
    )
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ExpenseSource.MANUAL.value, index=True
    )
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    billing_period_start: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    billing_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    usage_quantity: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    usage_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ExpenseStatus.ACTIVE.value, index=True
    )
    recurring_rule_id: Mapped[int | None] = mapped_column(
        ForeignKey("recurring_expense_rules.id"), nullable=True, index=True
    )
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    expense_type: Mapped["ExpenseType"] = relationship(back_populates="records")
    resource_account: Mapped["ResourceAccount | None"] = relationship()
    recurring_rule: Mapped["RecurringExpenseRule | None"] = relationship(back_populates="generated_records")
    distributions: Mapped[list["ExpenseDistribution"]] = relationship(
        back_populates="expense_record",
        cascade="all, delete-orphan",
    )
