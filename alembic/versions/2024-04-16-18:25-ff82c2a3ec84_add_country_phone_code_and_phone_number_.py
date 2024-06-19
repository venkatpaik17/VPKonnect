"""Add country_phone_code and phone_number columns to user table

Revision ID: ff82c2a3ec84
Revises: 7a9e4afd790d
Create Date: 2024-04-16 18:25:18.426031

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ff82c2a3ec84"
down_revision: Union[str, None] = "7a9e4afd790d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column(
            "country_phone_code",
            sa.String(length=10),
            nullable=True,
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "phone_number",
            sa.String(length=12),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("user", "phone_number")
    op.drop_column("user", "country_phone_code")
