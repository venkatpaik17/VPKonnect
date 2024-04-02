"""Create a table for maintaining content that are flagged for account type report, account_report_flagged_content

Revision ID: 2ecce19d2b31
Revises: 4e4a76b89b65
Create Date: 2024-03-29 15:01:31.759921

"""

from email.policy import default
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2ecce19d2b31"
down_revision: Union[str, None] = "4e4a76b89b65"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "account_report_flagged_content",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            nullable=False,
            server_default=sa.func.generate_ulid(),
        ),
        sa.Column(
            "flagged_content",
            ARRAY(UUID(as_uuid=True), dimensions=1),
            nullable=False,
            default=[],
        ),
        sa.Column(
            "valid_flagged_content",
            ARRAY(UUID(as_uuid=True), dimensions=1),
            nullable=False,
            default=[],
        ),
        sa.Column("report_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("False")
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["report_id"], ["user_content_report_detail.id"], ondelete="CASCADE"
        ),
    )


def downgrade() -> None:
    op.drop_table("account_report_flagged_content")
