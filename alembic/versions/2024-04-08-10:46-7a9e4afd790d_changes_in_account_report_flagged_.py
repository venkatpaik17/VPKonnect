"""changes in account_report_flagged_content table

Revision ID: 7a9e4afd790d
Revises: bcab7556473a
Create Date: 2024-04-08 10:46:37.327562

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7a9e4afd790d"
down_revision: Union[str, None] = "bcab7556473a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("account_report_flagged_content", "flagged_content")
    op.drop_column("account_report_flagged_content", "valid_flagged_content")

    op.add_column(
        "account_report_flagged_content",
        sa.Column("valid_flagged_content", UUID(as_uuid=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("account_report_flagged_content", "valid_flagged_content")

    op.add_column(
        "account_report_flagged_content",
        sa.Column(
            "valid_flagged_content",
            ARRAY(UUID(as_uuid=True), dimensions=1),
            nullable=False,
            default=[],
        ),
    )
    op.add_column(
        "account_report_flagged_content",
        sa.Column(
            "flagged_content",
            ARRAY(UUID(as_uuid=True), dimensions=1),
            nullable=False,
            default=[],
        ),
    )
