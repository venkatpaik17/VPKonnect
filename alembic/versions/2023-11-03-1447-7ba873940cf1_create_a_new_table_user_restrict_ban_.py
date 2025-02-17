"""Create a new table 'user_restrict_ban_detail' for storing restricted/banned user details for tracking restrictions

Revision ID: 7ba873940cf1
Revises: 34044c848904
Create Date: 2023-11-03 14:47:06.644442

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7ba873940cf1"
down_revision: Union[str, None] = "34044c848904"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_restrict_ban_detail",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            nullable=False,
            server_default=sa.func.generate_ulid(),
        ),
        sa.Column("status", sa.String(length=3), nullable=False),
        sa.Column("duration", sa.Integer, nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            onupdate=sa.func.now(),
        ),
        sa.Column(
            "is_deleted", sa.Boolean, nullable=False, server_default=sa.text("False")
        ),
        sa.Column(
            "is_violation", sa.Boolean, nullable=False, server_default=sa.text("True")
        ),
        sa.Column(
            "is_active", sa.Boolean, nullable=False, server_default=sa.text("True")
        ),
        sa.Column("content_type", sa.String, nullable=False),
        sa.Column("content_id", UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("user_restrict_ban_detail")
