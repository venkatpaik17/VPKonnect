"""drop two tables, post_activity and comment_activity

Revision ID: 1feb08c65e82
Revises: 4ad88eed5c12
Create Date: 2024-06-28 12:32:34.774895

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1feb08c65e82"
down_revision: Union[str, None] = "4ad88eed5c12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("post_activity")
    op.drop_table("comment_activity")


def downgrade() -> None:
    op.create_table(
        "comment_activity",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.func.generate_ulid(),
            nullable=False,
        ),
        sa.Column(
            "total_likes", sa.BigInteger(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("comment_id", UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["comment_id"], ["comment.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "post_activity",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.func.generate_ulid(),
            nullable=False,
        ),
        sa.Column(
            "total_likes", sa.BigInteger(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "total_comments",
            sa.BigInteger(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("post_id", UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["post.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
