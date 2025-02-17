"""Restrict the length of values for report_reason column and  add report_reason_user_id column to user_content_report_detail

Revision ID: ae1d86209d67
Revises: 709444c0d97c
Create Date: 2024-02-08 12:45:38.235673

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ae1d86209d67"
down_revision: Union[str, None] = "709444c0d97c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # modify type of report_reason
    op.alter_column(
        "user_content_report_detail",
        "report_reason",
        existing_type=sa.String(),
        type_=sa.String(length=10),
    )

    # add column report_reason_additional_data
    op.add_column(
        "user_content_report_detail",
        sa.Column("report_reason_user_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "user_content_report_detail_report_reason_user_id_fkey",
        "user_content_report_detail",
        "user",
        ["report_reason_user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "user_content_report_detail_report_reason_user_id_fkey",
        "user_content_report_detail",
        type_="foreignkey",
    )
    op.drop_column("user_content_report_detail", "report_reason_user_id")
    op.alter_column(
        "user_content_report_detail",
        "report_reason",
        existing_type=sa.String(length=10),
        type_=sa.String(),
    )
