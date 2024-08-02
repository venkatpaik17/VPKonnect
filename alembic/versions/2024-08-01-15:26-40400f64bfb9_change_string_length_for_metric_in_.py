"""change string length for metric in activity_detail table

Revision ID: 40400f64bfb9
Revises: 8d9d3ff468dc
Create Date: 2024-08-01 15:26:56.862843

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "40400f64bfb9"
down_revision: Union[str, None] = "8d9d3ff468dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "activity_detail",
        "metric",
        existing_type=sa.String(length=20),
        type_=sa.String(length=50),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "activity_detail",
        "metric",
        existing_type=sa.String(length=50),
        type_=sa.String(length=20),
        nullable=False,
    )
