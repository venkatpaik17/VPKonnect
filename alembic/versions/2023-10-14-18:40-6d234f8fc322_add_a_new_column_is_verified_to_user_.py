"""Add a new column 'is_verified' to user table, create a new table user_verification_code_token, copy existing data from user_password_reset_token to this new table, delete user_password_reset_token table

Revision ID: 6d234f8fc322
Revises: 31274edd7054
Create Date: 2023-10-14 18:40:17.396761

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6d234f8fc322"
down_revision: Union[str, None] = "31274edd7054"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="False"),
    )

    op.execute(
        """
               UPDATE "user" SET is_verified = TRUE
        """
    )

    op.alter_column("user", "status", server_default=sa.text("'INA'::user_status_enum"))

    op.create_table(
        "user_verification_code_token",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            unique=True,
            nullable=False,
            server_default=sa.func.generate_ulid(),
        ),
        sa.Column("code_token_id", sa.String, primary_key=True),
        sa.Column(
            "type",
            sa.String,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="False"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.execute(
        """
            INSERT INTO user_verification_code_token (id, code_token_id, type, user_id, is_deleted, created_at)
            SELECT id, reset_token_id, 'PWR', user_id, is_deleted, created_at
            FROM user_password_reset_token
        """
    )

    op.drop_table("user_password_reset_token")


def downgrade() -> None:
    op.create_table(
        "user_password_reset_token",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            unique=True,
            nullable=False,
            server_default=sa.func.generate_ulid(),
        ),
        sa.Column("reset_token_id", sa.String, primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="False"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.execute(
        """
            INSERT INTO user_password_reset_token (id, reset_token_id, user_id, is_deleted, created_at)
            SELECT id, code_token_id, user_id, is_deleted, created_at
            FROM user_verification_code_token
        """
    )

    op.drop_table("user_verification_code_token")

    op.alter_column("user", "status", server_default=sa.text("'ACT'::user_status_enum"))

    op.drop_column("user", "is_verified")
