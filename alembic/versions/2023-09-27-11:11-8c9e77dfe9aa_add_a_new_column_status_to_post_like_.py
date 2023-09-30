"""Add a new column 'status' to post_like and comment_like tables

Revision ID: 8c9e77dfe9aa
Revises: 1a5bffe2cc9e
Create Date: 2023-09-27 11:11:59.517264

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8c9e77dfe9aa"
down_revision: Union[str, None] = "1a5bffe2cc9e"
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
