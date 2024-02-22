"""Create tables user_content_report_detail and guideline_violation_score for storing reports and calculating violation scores to determine proper action

Revision ID: 0652caa9d4ab
Revises: 7ba873940cf1
Create Date: 2024-01-01 14:02:57.630268

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0652caa9d4ab"
down_revision: Union[str, None] = "7ba873940cf1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_content_report_detail",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            nullable=False,
            server_default=sa.func.generate_ulid(),
        ),
        sa.Column("reporter_user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("reported_item_id", UUID(as_uuid=True), nullable=False),
        sa.Column("reported_item_type", sa.String(), nullable=False),
        sa.Column("reported_user_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "case_number",
            sa.BigInteger(),
            nullable=False,
            server_default=sa.func.get_next_value_from_sequence(),
        ),
        sa.Column("report_reason", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=3),
            nullable=False,
            server_default=sa.text("'OPN'"),
        ),
        sa.Column("moderator_note", sa.String(), nullable=True),
        sa.Column(
            "is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("False")
        ),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["reporter_user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reported_user_id"], ["user.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "guideline_violation_score",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            nullable=False,
            server_default=sa.func.generate_ulid(),
        ),
        sa.Column(
            "post_score", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "comment_score", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "message_score", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "final_violation_score",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("guideline_violation_score")
    op.drop_table("user_content_report_detail")
