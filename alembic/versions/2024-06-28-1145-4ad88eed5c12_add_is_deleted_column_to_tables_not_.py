"""add is_deleted column to tables not having it

Revision ID: 4ad88eed5c12
Revises: ff82c2a3ec84
Create Date: 2024-06-28 11:45:57.201960

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4ad88eed5c12"
down_revision: Union[str, None] = "ff82c2a3ec84"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employee_auth_track",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="False"),
    )
    op.add_column(
        "employee_session",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="False"),
    )
    op.add_column(
        "guideline_violation_score",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="False"),
    )
    op.add_column(
        "password_change_history",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="False"),
    )
    op.add_column(
        "user_account_history",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="False"),
    )
    op.add_column(
        "user_auth_track",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="False"),
    )
    op.add_column(
        "user_session",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="False"),
    )
    op.add_column(
        "user_follow_association",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="False"),
    )
    op.add_column(
        "username_change_history",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="False"),
    )


def downgrade() -> None:
    op.drop_column("username_change_history", "is_deleted")
    op.drop_column("user_follow_association", "is_deleted")
    op.drop_column("user_session", "is_deleted")
    op.drop_column("user_auth_track", "is_deleted")
    op.drop_column("user_account_history", "is_deleted")
    op.drop_column("password_change_history", "is_deleted")
    op.drop_column("guideline_violation_score", "is_deleted")
    op.drop_column("employee_session", "is_deleted")
    op.drop_column("employee_auth_track", "is_deleted")
