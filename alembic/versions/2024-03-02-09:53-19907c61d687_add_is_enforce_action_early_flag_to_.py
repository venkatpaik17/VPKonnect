"""Add is_enforce_action_early flag to user_restrict_ban_detail table to determine whether action is enforced earlier than it's datetime

Revision ID: 19907c61d687
Revises: a70e1432c160
Create Date: 2024-03-02 09:53:20.915308

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "19907c61d687"
down_revision: Union[str, None] = "a70e1432c160"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_restrict_ban_detail",
        sa.Column(
            "is_enforce_action_early",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("False"),
        ),
    )


def downgrade() -> None:
    op.drop_column("user_restrict_ban_detail", "is_enforce_action_early")
