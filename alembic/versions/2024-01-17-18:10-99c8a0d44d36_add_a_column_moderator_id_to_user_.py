"""Add a column moderator_id to user_content_report_detail table

Revision ID: 99c8a0d44d36
Revises: 0652caa9d4ab
Create Date: 2024-01-17 18:10:28.739892

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "99c8a0d44d36"
down_revision: Union[str, None] = "0652caa9d4ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_content_report_detail",
        sa.Column(
            "moderator_id",
            UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("user_content_report_detail", "moderator_id")
