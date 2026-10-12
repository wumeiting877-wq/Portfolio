"""gate3 resource types, accounts and allocations

Revision ID: 0004_gate3_resources
Revises: 0003_gate2_projects
Create Date: 2026-09-22
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_gate3_resources"
down_revision: Union[str, Sequence[str], None] = "0003_gate2_projects"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resource_types",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resource_types_code", "resource_types", ["code"], unique=True)
    op.create_index("ix_resource_types_category", "resource_types", ["category"], unique=False)
    op.create_index("ix_resource_types_is_active", "resource_types", ["is_active"], unique=False)

    op.create_table(
        "resource_accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resource_type_id", sa.Integer(), nullable=False),
        sa.Column("resource_name", sa.String(length=200), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=True),
        sa.Column("account_identifier", sa.String(length=200), nullable=True),
        sa.Column("plan_name", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("purchased_at", sa.Date(), nullable=True),
        sa.Column("activated_at", sa.Date(), nullable=True),
        sa.Column("expires_at", sa.Date(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["resource_type_id"], ["resource_types.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resource_accounts_resource_type_id", "resource_accounts", ["resource_type_id"], unique=False)
    op.create_index("ix_resource_accounts_resource_name", "resource_accounts", ["resource_name"], unique=False)
    op.create_index("ix_resource_accounts_status", "resource_accounts", ["status"], unique=False)
    op.create_index("ix_resource_accounts_expires_at", "resource_accounts", ["expires_at"], unique=False)

    op.create_table(
        "resource_allocations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resource_account_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("employee_id", sa.Integer(), nullable=True),
        sa.Column("allocated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "project_id IS NOT NULL OR employee_id IS NOT NULL",
            name="ck_resource_allocations_has_target",
        ),
        sa.ForeignKeyConstraint(["resource_account_id"], ["resource_accounts.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_resource_allocations_resource_account_id",
        "resource_allocations",
        ["resource_account_id"],
        unique=False,
    )
    op.create_index("ix_resource_allocations_project_id", "resource_allocations", ["project_id"], unique=False)
    op.create_index("ix_resource_allocations_employee_id", "resource_allocations", ["employee_id"], unique=False)
    op.create_index("ix_resource_allocations_is_active", "resource_allocations", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_resource_allocations_is_active", table_name="resource_allocations")
    op.drop_index("ix_resource_allocations_employee_id", table_name="resource_allocations")
    op.drop_index("ix_resource_allocations_project_id", table_name="resource_allocations")
    op.drop_index("ix_resource_allocations_resource_account_id", table_name="resource_allocations")
    op.drop_table("resource_allocations")
    op.drop_index("ix_resource_accounts_expires_at", table_name="resource_accounts")
    op.drop_index("ix_resource_accounts_status", table_name="resource_accounts")
    op.drop_index("ix_resource_accounts_resource_name", table_name="resource_accounts")
    op.drop_index("ix_resource_accounts_resource_type_id", table_name="resource_accounts")
    op.drop_table("resource_accounts")
    op.drop_index("ix_resource_types_is_active", table_name="resource_types")
    op.drop_index("ix_resource_types_category", table_name="resource_types")
    op.drop_index("ix_resource_types_code", table_name="resource_types")
    op.drop_table("resource_types")
