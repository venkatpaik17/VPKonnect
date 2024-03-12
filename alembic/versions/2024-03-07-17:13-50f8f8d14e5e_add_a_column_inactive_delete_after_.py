"""Add a column inactive_delete_after column to user table

Revision ID: 50f8f8d14e5e
Revises: ef3acf1429b2
Create Date: 2024-03-07 17:13:14.397125

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "50f8f8d14e5e"
down_revision: Union[str, None] = "ef3acf1429b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column(
            "inactive_delete_after",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("183"),
        ),
    )


def downgrade() -> None:
    op.drop_column("user", "inactive_delete_after")
