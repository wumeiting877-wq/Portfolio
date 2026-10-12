"""gate4 expense types, records, distributions and recurring rules

Revision ID: 0005_gate4_expenses
Revises: 0004_gate3_resources
Create Date: 2026-09-22
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_gate4_expenses"
down_revision: Union[str, Sequence[str], None] = "0004_gate3_resources"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "expense_types",
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
    op.create_index("ix_expense_types_code", "expense_types", ["code"], unique=True)
    op.create_index("ix_expense_types_category", "expense_types", ["category"], unique=False)
    op.create_index("ix_expense_types_is_active", "expense_types", ["is_active"], unique=False)

    op.create_table(
        "recurring_expense_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("expense_type_id", sa.Integer(), nullable=False),
        sa.Column("resource_account_id", sa.Integer(), nullable=True),
        sa.Column("frequency", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("next_run_date", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("default_distribution_mode", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["expense_type_id"], ["expense_types.id"]),
        sa.ForeignKeyConstraint(["resource_account_id"], ["resource_accounts.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recurring_expense_rules_expense_type_id", "recurring_expense_rules", ["expense_type_id"])
    op.create_index(
        "ix_recurring_expense_rules_resource_account_id",
        "recurring_expense_rules",
        ["resource_account_id"],
    )
    op.create_index("ix_recurring_expense_rules_frequency", "recurring_expense_rules", ["frequency"])
    op.create_index("ix_recurring_expense_rules_next_run_date", "recurring_expense_rules", ["next_run_date"])
    op.create_index("ix_recurring_expense_rules_is_active", "recurring_expense_rules", ["is_active"])

    op.create_table(
        "recurring_rule_distributions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("rule_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("employee_id", sa.Integer(), nullable=True),
        sa.Column("allocation_method", sa.String(length=20), nullable=False),
        sa.Column("allocation_ratio", sa.Numeric(18, 6), nullable=True),
        sa.Column("allocated_amount", sa.Numeric(18, 4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "project_id IS NOT NULL OR employee_id IS NOT NULL",
            name="ck_recurring_rule_distributions_has_target",
        ),
        sa.ForeignKeyConstraint(["rule_id"], ["recurring_expense_rules.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recurring_rule_distributions_rule_id", "recurring_rule_distributions", ["rule_id"])
    op.create_index("ix_recurring_rule_distributions_project_id", "recurring_rule_distributions", ["project_id"])
    op.create_index("ix_recurring_rule_distributions_employee_id", "recurring_rule_distributions", ["employee_id"])

    op.create_table(
        "expense_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("expense_type_id", sa.Integer(), nullable=False),
        sa.Column("resource_account_id", sa.Integer(), nullable=True),
        sa.Column("billing_mode", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("billing_period_start", sa.Date(), nullable=True),
        sa.Column("billing_period_end", sa.Date(), nullable=True),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("usage_quantity", sa.Numeric(18, 6), nullable=True),
        sa.Column("usage_unit", sa.String(length=50), nullable=True),
        sa.Column("unit_price", sa.Numeric(18, 6), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("external_reference", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("recurring_rule_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["expense_type_id"], ["expense_types.id"]),
        sa.ForeignKeyConstraint(["resource_account_id"], ["resource_accounts.id"]),
        sa.ForeignKeyConstraint(["recurring_rule_id"], ["recurring_expense_rules.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_expense_records_expense_type_id", "expense_records", ["expense_type_id"])
    op.create_index("ix_expense_records_resource_account_id", "expense_records", ["resource_account_id"])
    op.create_index("ix_expense_records_billing_mode", "expense_records", ["billing_mode"])
    op.create_index("ix_expense_records_source", "expense_records", ["source"])
    op.create_index("ix_expense_records_expense_date", "expense_records", ["expense_date"])
    op.create_index("ix_expense_records_billing_period_start", "expense_records", ["billing_period_start"])
    op.create_index("ix_expense_records_currency", "expense_records", ["currency"])
    op.create_index("ix_expense_records_status", "expense_records", ["status"])
    op.create_index("ix_expense_records_recurring_rule_id", "expense_records", ["recurring_rule_id"])
    op.create_index(
        "uq_expense_records_recurring_period",
        "expense_records",
        ["recurring_rule_id", "billing_period_start"],
        unique=True,
        postgresql_where=sa.text("recurring_rule_id IS NOT NULL AND billing_period_start IS NOT NULL"),
    )

    op.create_table(
        "expense_distributions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("expense_record_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("employee_id", sa.Integer(), nullable=True),
        sa.Column("allocation_method", sa.String(length=20), nullable=False),
        sa.Column("allocation_ratio", sa.Numeric(18, 6), nullable=True),
        sa.Column("allocated_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "project_id IS NOT NULL OR employee_id IS NOT NULL",
            name="ck_expense_distributions_has_target",
        ),
        sa.CheckConstraint(
            "allocated_amount >= 0",
            name="ck_expense_distributions_amount_non_negative",
        ),
        sa.ForeignKeyConstraint(["expense_record_id"], ["expense_records.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_expense_distributions_expense_record_id", "expense_distributions", ["expense_record_id"])
    op.create_index("ix_expense_distributions_project_id", "expense_distributions", ["project_id"])
    op.create_index("ix_expense_distributions_employee_id", "expense_distributions", ["employee_id"])


def downgrade() -> None:
    op.drop_index("ix_expense_distributions_employee_id", table_name="expense_distributions")
    op.drop_index("ix_expense_distributions_project_id", table_name="expense_distributions")
    op.drop_index("ix_expense_distributions_expense_record_id", table_name="expense_distributions")
    op.drop_table("expense_distributions")
    op.drop_index("uq_expense_records_recurring_period", table_name="expense_records")
    op.drop_index("ix_expense_records_recurring_rule_id", table_name="expense_records")
    op.drop_index("ix_expense_records_status", table_name="expense_records")
    op.drop_index("ix_expense_records_currency", table_name="expense_records")
    op.drop_index("ix_expense_records_billing_period_start", table_name="expense_records")
    op.drop_index("ix_expense_records_expense_date", table_name="expense_records")
    op.drop_index("ix_expense_records_source", table_name="expense_records")
    op.drop_index("ix_expense_records_billing_mode", table_name="expense_records")
    op.drop_index("ix_expense_records_resource_account_id", table_name="expense_records")
    op.drop_index("ix_expense_records_expense_type_id", table_name="expense_records")
    op.drop_table("expense_records")
    op.drop_index("ix_recurring_rule_distributions_employee_id", table_name="recurring_rule_distributions")
    op.drop_index("ix_recurring_rule_distributions_project_id", table_name="recurring_rule_distributions")
    op.drop_index("ix_recurring_rule_distributions_rule_id", table_name="recurring_rule_distributions")
    op.drop_table("recurring_rule_distributions")
    op.drop_index("ix_recurring_expense_rules_is_active", table_name="recurring_expense_rules")
    op.drop_index("ix_recurring_expense_rules_next_run_date", table_name="recurring_expense_rules")
    op.drop_index("ix_recurring_expense_rules_frequency", table_name="recurring_expense_rules")
    op.drop_index("ix_recurring_expense_rules_resource_account_id", table_name="recurring_expense_rules")
    op.drop_index("ix_recurring_expense_rules_expense_type_id", table_name="recurring_expense_rules")
    op.drop_table("recurring_expense_rules")
    op.drop_index("ix_expense_types_is_active", table_name="expense_types")
    op.drop_index("ix_expense_types_category", table_name="expense_types")
    op.drop_index("ix_expense_types_code", table_name="expense_types")
    op.drop_table("expense_types")
