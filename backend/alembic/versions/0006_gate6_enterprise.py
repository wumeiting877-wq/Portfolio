"""gate6 notifications and system settings

Revision ID: 0006_gate6_enterprise
Revises: 0005_gate4_expenses
Create Date: 2026-09-22
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_gate6_enterprise"
down_revision: Union[str, Sequence[str], None] = "0005_gate4_expenses"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=200), nullable=False, server_default="项目费用中枢"),
        sa.Column("default_currency", sa.String(length=8), nullable=False, server_default="CNY"),
        sa.Column("business_timezone", sa.String(length=64), nullable=False, server_default="Asia/Shanghai"),
        sa.Column("expiring_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("page_size_default", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO system_settings (
                id, company_name, default_currency, business_timezone,
                expiring_days, page_size_default
            )
            VALUES (1, '项目费用中枢', 'CNY', 'Asia/Shanghai', 30, 20)
            """
        )
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.String(length=50), nullable=False),
        sa.Column("period_key", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="UNREAD"),
        sa.Column("resource_account_id", sa.Integer(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["resource_account_id"], ["resource_accounts.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "type",
            "target_type",
            "target_id",
            "period_key",
            name="uq_notifications_idempotency",
        ),
    )
    op.create_index("ix_notifications_type", "notifications", ["type"], unique=False)
    op.create_index("ix_notifications_status", "notifications", ["status"], unique=False)
    op.create_index("ix_notifications_period_key", "notifications", ["period_key"], unique=False)
    op.create_index(
        "ix_notifications_resource_account_id",
        "notifications",
        ["resource_account_id"],
        unique=False,
    )
    op.create_index("ix_notifications_project_id", "notifications", ["project_id"], unique=False)
    op.create_index("ix_notifications_due_date", "notifications", ["due_date"], unique=False)
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_due_date", table_name="notifications")
    op.drop_index("ix_notifications_project_id", table_name="notifications")
    op.drop_index("ix_notifications_resource_account_id", table_name="notifications")
    op.drop_index("ix_notifications_period_key", table_name="notifications")
    op.drop_index("ix_notifications_status", table_name="notifications")
    op.drop_index("ix_notifications_type", table_name="notifications")
    op.drop_table("notifications")
    op.drop_table("system_settings")
