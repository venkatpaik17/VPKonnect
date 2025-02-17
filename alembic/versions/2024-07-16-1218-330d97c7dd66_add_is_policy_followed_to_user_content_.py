"""add is_policy_followed to user_content_restrict_ban_appeal_detail table

Revision ID: 330d97c7dd66
Revises: 9e03ded571b4
Create Date: 2024-07-16 12:18:48.701137

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "330d97c7dd66"
down_revision: Union[str, None] = "9e03ded571b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_content_restrict_ban_appeal_detail",
        sa.Column("is_policy_followed", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_content_restrict_ban_appeal_detail", "is_policy_followed")
