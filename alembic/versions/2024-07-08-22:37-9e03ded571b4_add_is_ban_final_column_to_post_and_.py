"""add is_ban_final column to post and comment table

Revision ID: 9e03ded571b4
Revises: 1feb08c65e82
Create Date: 2024-07-08 22:37:39.366136

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9e03ded571b4"
down_revision: Union[str, None] = "1feb08c65e82"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "post",
        sa.Column("is_ban_final", sa.Boolean(), nullable=False, server_default="False"),
    )
    op.add_column(
        "comment",
        sa.Column("is_ban_final", sa.Boolean(), nullable=False, server_default="False"),
    )


def downgrade() -> None:
    op.drop_column("comment", "is_ban_final")
    op.drop_column("post", "is_ban_final")
