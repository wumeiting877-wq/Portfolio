"""resource credential data model and grants

Revision ID: 0008_resource_credentials
Revises: 0007_resource_name_unique
Create Date: 2026-09-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_resource_credentials"
down_revision: Union[str, Sequence[str], None] = "0007_resource_name_unique"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resource_credentials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resource_account_id", sa.Integer(), nullable=False),
        sa.Column("credential_name", sa.String(length=200), nullable=False),
        sa.Column("credential_type", sa.String(length=32), nullable=False),
        sa.Column("encrypted_payload", sa.LargeBinary(), nullable=False),
        sa.Column("encryption_nonce", sa.LargeBinary(), nullable=False),
        sa.Column("encryption_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("key_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rotation_interval_days", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "rotation_interval_days IS NULL OR rotation_interval_days > 0",
            name="ck_resource_credentials_rotation_positive",
        ),
        sa.CheckConstraint(
            "credential_type IN ('USERNAME_PASSWORD','API_KEY','ACCESS_TOKEN','CLIENT_CREDENTIAL','SSH_KEY','OTHER')",
            name="ck_resource_credentials_type",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE','EXPIRED','DISABLED')",
            name="ck_resource_credentials_status",
        ),
        sa.ForeignKeyConstraint(["resource_account_id"], ["resource_accounts.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "resource_account_id",
            "credential_name",
            name="uq_resource_credentials_resource_name",
        ),
    )
    op.create_index("ix_resource_credentials_resource_account_id", "resource_credentials", ["resource_account_id"])
    op.create_index("ix_resource_credentials_status", "resource_credentials", ["status"])
    op.create_index("ix_resource_credentials_expires_at", "resource_credentials", ["expires_at"])

    op.create_table(
        "resource_credential_grants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("credential_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("can_reveal", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("granted_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["credential_id"], ["resource_credentials.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["granted_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "credential_id",
            "user_id",
            name="uq_resource_credential_grants_credential_user",
        ),
    )
    op.create_index("ix_resource_credential_grants_credential_id", "resource_credential_grants", ["credential_id"])
    op.create_index("ix_resource_credential_grants_user_id", "resource_credential_grants", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_resource_credential_grants_user_id", table_name="resource_credential_grants")
    op.drop_index("ix_resource_credential_grants_credential_id", table_name="resource_credential_grants")
    op.drop_table("resource_credential_grants")
    op.drop_index("ix_resource_credentials_expires_at", table_name="resource_credentials")
    op.drop_index("ix_resource_credentials_status", table_name="resource_credentials")
    op.drop_index("ix_resource_credentials_resource_account_id", table_name="resource_credentials")
    op.drop_table("resource_credentials")
