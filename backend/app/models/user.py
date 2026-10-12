from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import UserStatus

if TYPE_CHECKING:
    from app.models.resource_credential import ResourceCredential
    from app.models.resource_credential_grant import ResourceCredentialGrant


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id"), unique=True, nullable=True
    )
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=UserStatus.ACTIVE.value, index=True
    )
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    employee: Mapped["Employee | None"] = relationship(back_populates="user")
    role: Mapped["Role"] = relationship(back_populates="users")
    credentials_created: Mapped[list["ResourceCredential"]] = relationship(
        foreign_keys="ResourceCredential.created_by_user_id",
        back_populates="created_by_user",
    )
    credentials_updated: Mapped[list["ResourceCredential"]] = relationship(
        foreign_keys="ResourceCredential.updated_by_user_id",
        back_populates="updated_by_user",
    )
    credential_grants: Mapped[list["ResourceCredentialGrant"]] = relationship(
        foreign_keys="ResourceCredentialGrant.user_id",
        back_populates="user",
    )
    credential_grants_issued: Mapped[list["ResourceCredentialGrant"]] = relationship(
        foreign_keys="ResourceCredentialGrant.granted_by_user_id",
        back_populates="granted_by_user",
    )
