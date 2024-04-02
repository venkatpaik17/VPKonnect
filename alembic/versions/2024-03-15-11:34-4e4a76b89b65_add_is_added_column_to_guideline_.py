"""add is_added column to guideline_violation_last_added_score table

Revision ID: 4e4a76b89b65
Revises: 50f8f8d14e5e
Create Date: 2024-03-15 11:34:27.311666

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4e4a76b89b65"
down_revision: Union[str, None] = "50f8f8d14e5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "guideline_violation_last_added_score",
        sa.Column(
            "is_added", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")
        ),
    )

    op.execute("UPDATE guideline_violation_last_added_score SET is_added = TRUE")


def downgrade() -> None:
    op.drop_column("guideline_violation_last_added_score", "is_added")
