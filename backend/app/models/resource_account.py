from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ResourceStatus

if TYPE_CHECKING:
    from app.models.resource_credential import ResourceCredential
    from app.models.resource_allocation import ResourceAllocation
    from app.models.resource_type import ResourceType


class ResourceAccount(Base):
    __tablename__ = "resource_accounts"
    __table_args__ = (
        Index("uq_resource_accounts_resource_name", "resource_name", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resource_type_id: Mapped[int] = mapped_column(
        ForeignKey("resource_types.id"), nullable=False, index=True
    )
    resource_name: Mapped[str] = mapped_column(String(200), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    account_identifier: Mapped[str | None] = mapped_column(String(200), nullable=True)
    plan_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ResourceStatus.ACTIVE.value, index=True
    )
    purchased_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    activated_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    expires_at: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    resource_type: Mapped["ResourceType"] = relationship(back_populates="accounts")
    allocations: Mapped[list["ResourceAllocation"]] = relationship(back_populates="resource")
    credentials: Mapped[list["ResourceCredential"]] = relationship(back_populates="resource_account")
