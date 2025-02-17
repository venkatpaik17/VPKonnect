"""Add a new column 'status' to post_like and comment_like tables

Revision ID: 2628aa36e527
Revises: 60fe7fae86c7
Create Date: 2023-10-30 10:35:00.319082

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2628aa36e527"
down_revision: Union[str, None] = "60fe7fae86c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "post_like",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'active'"),
        ),
    )
    op.add_column(
        "comment_like",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'active'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("post_like", "status")
    op.drop_column("comment_like", "status")
