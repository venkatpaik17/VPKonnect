"""remove is_violation column and add enforce_action_at column to user_restrict_ban_detail table, add last_added_score column to guideline_violation_score

Revision ID: a12c9097a872
Revises: 7517b1487cf9
Create Date: 2024-02-12 12:08:32.571184

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a12c9097a872"
down_revision: Union[str, None] = "7517b1487cf9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("user_restrict_ban_detail", "is_violation")
    op.add_column(
        "user_restrict_ban_detail",
        sa.Column("enforce_action_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )

    op.add_column(
        "guideline_violation_score",
        sa.Column(
            "last_added_score",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    op.drop_column("guideline_violation_score", "last_added_score")

    op.drop_column("user_restrict_ban_detail", "enforce_action_at")
    op.add_column(
        "user_restrict_ban_detail",
        sa.Column(
            "is_violation", sa.Boolean, nullable=False, server_default=sa.text("True")
        ),
    )
