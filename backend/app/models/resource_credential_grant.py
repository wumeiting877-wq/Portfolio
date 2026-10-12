from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.resource_credential import ResourceCredential
    from app.models.user import User


class ResourceCredentialGrant(Base):
    __tablename__ = "resource_credential_grants"
    __table_args__ = (
        UniqueConstraint("credential_id", "user_id", name="uq_resource_credential_grants_credential_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    credential_id: Mapped[int] = mapped_column(ForeignKey("resource_credentials.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    can_reveal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    granted_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    credential: Mapped["ResourceCredential"] = relationship(back_populates="grants")
    user: Mapped["User"] = relationship(foreign_keys=[user_id], back_populates="credential_grants")
    granted_by_user: Mapped["User"] = relationship(
        foreign_keys=[granted_by_user_id], back_populates="credential_grants_issued"
    )
