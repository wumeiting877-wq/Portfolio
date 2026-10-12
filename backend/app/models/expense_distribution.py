from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AllocationMethod

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.expense_record import ExpenseRecord
    from app.models.project import Project


class ExpenseDistribution(Base):
    __tablename__ = "expense_distributions"
    __table_args__ = (
        CheckConstraint(
            "project_id IS NOT NULL OR employee_id IS NOT NULL",
            name="ck_expense_distributions_has_target",
        ),
        CheckConstraint(
            "allocated_amount >= 0",
            name="ck_expense_distributions_amount_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    expense_record_id: Mapped[int] = mapped_column(
        ForeignKey("expense_records.id"), nullable=False, index=True
    )
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True, index=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True, index=True)
    allocation_method: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AllocationMethod.DIRECT.value
    )
    allocation_ratio: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    expense_record: Mapped["ExpenseRecord"] = relationship(back_populates="distributions")
    project: Mapped["Project | None"] = relationship()
    employee: Mapped["Employee | None"] = relationship()
