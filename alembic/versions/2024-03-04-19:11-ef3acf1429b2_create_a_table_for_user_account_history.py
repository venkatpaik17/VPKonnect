"""Create a table for user account history

Revision ID: ef3acf1429b2
Revises: c87b43a2530b
Create Date: 2024-03-04 19:11:34.620166

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ef3acf1429b2"
down_revision: Union[str, None] = "c87b43a2530b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_account_history",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            nullable=False,
            server_default=sa.func.generate_ulid(),
        ),
        sa.Column("account_detail_type", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("new_detail_value", sa.String(), nullable=True),
        sa.Column("previous_detail_value", sa.String(), nullable=True),
        sa.Column("device_info", sa.String(), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("user_account_history")
