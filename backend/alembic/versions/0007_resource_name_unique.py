"""resource_accounts.resource_name unique

Revision ID: 0007_resource_name_unique
Revises: 0006_gate6_enterprise
Create Date: 2026-09-23

Historical duplicate names are kept. Later rows of the same name are
renamed to "<name> #<id>" so the unique index can be created without
deleting any resource.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_resource_name_unique"
down_revision: Union[str, Sequence[str], None] = "0006_gate6_enterprise"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE resource_accounts AS ra
            SET resource_name = left(ra.resource_name, 200 - char_length(' #' || ra.id::text))
                || ' #' || ra.id::text
            FROM (
                SELECT id
                FROM (
                    SELECT id,
                           row_number() OVER (PARTITION BY resource_name ORDER BY id) AS rn
                    FROM resource_accounts
                ) ranked
                WHERE rn > 1
            ) dups
            WHERE ra.id = dups.id
            """
        )
    )
    op.drop_index("ix_resource_accounts_resource_name", table_name="resource_accounts")
    op.create_index(
        "uq_resource_accounts_resource_name",
        "resource_accounts",
        ["resource_name"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_resource_accounts_resource_name", table_name="resource_accounts")
    op.create_index(
        "ix_resource_accounts_resource_name",
        "resource_accounts",
        ["resource_name"],
        unique=False,
    )
