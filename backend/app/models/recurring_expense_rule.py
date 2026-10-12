from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AllocationMethod, RecurringFrequency

if TYPE_CHECKING:
    from app.models.expense_record import ExpenseRecord
    from app.models.expense_type import ExpenseType
    from app.models.recurring_rule_distribution import RecurringRuleDistribution
    from app.models.resource_account import ResourceAccount


class RecurringExpenseRule(Base):
    __tablename__ = "recurring_expense_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    expense_type_id: Mapped[int] = mapped_column(ForeignKey("expense_types.id"), nullable=False, index=True)
    resource_account_id: Mapped[int | None] = mapped_column(
        ForeignKey("resource_accounts.id"), nullable=True, index=True
    )
    frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, default=RecurringFrequency.MONTHLY.value, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_run_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    default_distribution_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AllocationMethod.DIRECT.value
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    expense_type: Mapped["ExpenseType"] = relationship(back_populates="recurring_rules")
    resource_account: Mapped["ResourceAccount | None"] = relationship()
    distributions: Mapped[list["RecurringRuleDistribution"]] = relationship(
        back_populates="rule",
        cascade="all, delete-orphan",
    )
    generated_records: Mapped[list["ExpenseRecord"]] = relationship(back_populates="recurring_rule")
