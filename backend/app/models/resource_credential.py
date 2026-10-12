from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, LargeBinary, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import CredentialStatus, CredentialType

if TYPE_CHECKING:
    from app.models.resource_account import ResourceAccount
    from app.models.resource_credential_grant import ResourceCredentialGrant
    from app.models.user import User


class ResourceCredential(Base):
    __tablename__ = "resource_credentials"
    __table_args__ = (
        UniqueConstraint(
            "resource_account_id",
            "credential_name",
            name="uq_resource_credentials_resource_name",
        ),
        CheckConstraint("rotation_interval_days IS NULL OR rotation_interval_days > 0", name="ck_resource_credentials_rotation_positive"),
        CheckConstraint(
            "credential_type IN ('USERNAME_PASSWORD','API_KEY','ACCESS_TOKEN','CLIENT_CREDENTIAL','SSH_KEY','OTHER')",
            name="ck_resource_credentials_type",
        ),
        CheckConstraint(
            "status IN ('ACTIVE','EXPIRED','DISABLED')",
            name="ck_resource_credentials_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resource_account_id: Mapped[int] = mapped_column(
        ForeignKey("resource_accounts.id"), nullable=False, index=True
    )
    credential_name: Mapped[str] = mapped_column(String(200), nullable=False)
    credential_type: Mapped[str] = mapped_column(String(32), nullable=False)
    encrypted_payload: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    encryption_nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    encryption_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    key_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CredentialStatus.ACTIVE.value, index=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rotation_interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    resource_account: Mapped["ResourceAccount"] = relationship(back_populates="credentials")
    created_by_user: Mapped["User"] = relationship(
        foreign_keys=[created_by_user_id], back_populates="credentials_created"
    )
    updated_by_user: Mapped["User"] = relationship(
        foreign_keys=[updated_by_user_id], back_populates="credentials_updated"
    )
    grants: Mapped[list["ResourceCredentialGrant"]] = relationship(back_populates="credential")


def credential_audit_metadata(credential: ResourceCredential) -> dict[str, object]:
    """Build the only approved audit shape for credential records: metadata, never secrets."""
    return {
        "credential_id": credential.id,
        "credential_name": credential.credential_name,
        "credential_type": credential.credential_type,
        "resource_account_id": credential.resource_account_id,
        "status": credential.status,
        "expires_at": credential.expires_at.isoformat() if credential.expires_at else None,
        "last_rotated_at": (
            credential.last_rotated_at.isoformat() if credential.last_rotated_at else None
        ),
        "rotation_interval_days": credential.rotation_interval_days,
    }
