"""remove last_added_score from guideline_violation_score table and create a table for storing all last_added_score

Revision ID: c87b43a2530b
Revises: 5bd88146bc48
Create Date: 2024-03-02 14:24:25.264304

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c87b43a2530b"
down_revision: Union[str, None] = "5bd88146bc48"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("guideline_violation_score", "last_added_score")

    op.create_table(
        "guideline_violation_last_added_score",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            nullable=False,
            server_default=sa.func.generate_ulid(),
        ),
        sa.Column("last_added_score", sa.Integer(), nullable=False),
        sa.Column(
            "is_removed", sa.Boolean(), nullable=False, server_default=sa.text("False")
        ),
        sa.Column(
            "is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("False")
        ),
        sa.Column("score_id", UUID(as_uuid=True), nullable=False),
        sa.Column("report_id", UUID(as_uuid=True), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["score_id"], ["guideline_violation_score.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["report_id"], ["user_content_report_detail.id"], ondelete="CASCADE"
        ),
    )


def downgrade() -> None:
    op.drop_table("guideline_violation_last_added_score")
    op.add_column(
        "guideline_violation_score",
        sa.Column(
            "last_added_score",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
