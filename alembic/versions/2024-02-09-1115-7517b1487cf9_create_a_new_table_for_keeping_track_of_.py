"""Create a new table for keeping track of user content report events, user_content_report_event_timeline. Add a new column report_id to
   user_restrict_ban_detail table as a foreign key to id in user_content_report_detail table

Revision ID: 7517b1487cf9
Revises: ae1d86209d67
Create Date: 2024-02-09 11:15:24.221745

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7517b1487cf9"
down_revision: Union[str, None] = "ae1d86209d67"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_restrict_ban_detail",
        sa.Column("report_id", UUID(as_uuid=True), nullable=False),
    )
    op.create_foreign_key(
        "user_restrict_ban_detail_report_id_fkey",
        "user_restrict_ban_detail",
        "user_content_report_detail",
        ["report_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_table(
        "user_content_report_event_timeline",
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
        sa.Column("report_id", UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["report_id"], ["user_content_report_detail.id"], ondelete="CASCADE"
        ),
    )


def downgrade() -> None:
    op.drop_table("user_content_report_event_timeline")

    op.drop_constraint(
        "user_restrict_ban_detail_report_id_fkey",
        "user_restrict_ban_detail",
        type_="foreignkey",
    )
    op.drop_column("user_restrict_ban_detail", "report_id")
