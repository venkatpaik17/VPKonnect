"""create a table for user content ban appeals

Revision ID: 72ac741431ff
Revises: a12c9097a872
Create Date: 2024-02-26 16:44:30.658720

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "72ac741431ff"
down_revision: Union[str, None] = "a12c9097a872"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_content_restrict_ban_appeal_detail",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            nullable=False,
            server_default=sa.func.generate_ulid(),
        ),
        sa.Column(
            "case_number",
            sa.BigInteger(),
            nullable=False,
            server_default=sa.func.get_next_value_from_sequence_ban_appeal_table(),
        ),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("report_id", UUID(as_uuid=True), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("content_id", UUID(as_uuid=True), nullable=False),
        sa.Column("appeal_detail", sa.String(), nullable=False),
        sa.Column("attachment", sa.String(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=3),
            nullable=False,
            server_default=sa.text("'OPN'"),
        ),
        sa.Column("moderator_id", UUID(as_uuid=True), nullable=True),
        sa.Column("moderator_note", sa.String(), nullable=True),
        sa.Column(
            "is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("False")
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            onupdate=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["moderator_id"], ["employee.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["report_id"], ["user_content_report_detail.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("case_number"),
    )


def downgrade() -> None:
    op.drop_table("user_content_restrict_ban_appeal_detail")
