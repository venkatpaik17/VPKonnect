"""add updated_at column to user_follow_association, post_like and comment_like

Revision ID: 429fe181bd71
Revises: 330d97c7dd66
Create Date: 2024-07-25 18:47:05.806429

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "429fe181bd71"
down_revision: Union[str, None] = "330d97c7dd66"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_follow_association",
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            onupdate=sa.func.now(),
        ),
    )
    op.add_column(
        "post_like",
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            onupdate=sa.func.now(),
        ),
    )
    op.add_column(
        "comment_like",
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            onupdate=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_column("comment_like", "updated_at")
    op.drop_column("post_like", "updated_at")
    op.drop_column("user_follow_association", "updated_at")
