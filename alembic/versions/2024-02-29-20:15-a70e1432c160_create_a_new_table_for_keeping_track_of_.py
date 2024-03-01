"""Create a new table for keeping track of user content appeal events, user_content_restrict_ban_appeal_event_timeline

Revision ID: a70e1432c160
Revises: 72ac741431ff
Create Date: 2024-02-29 20:15:01.770485

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a70e1432c160"
down_revision: Union[str, None] = "72ac741431ff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_content_restrict_ban_appeal_event_timeline",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            nullable=False,
            server_default=sa.func.generate_ulid(),
        ),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("detail", sa.String(), nullable=True),
        sa.Column("appeal_id", UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["appeal_id"],
            ["user_content_restrict_ban_appeal_detail.id"],
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    op.drop_table("user_content_restrict_ban_appeal_event_timeline")
