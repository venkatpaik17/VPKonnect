"""Create new tables employee_session and employee_auth_track

Revision ID: 78b50efef30c
Revises: 0a66adc196c5
Create Date: 2024-01-30 18:30:12.098867

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "78b50efef30c"
down_revision: Union[str, None] = "0a66adc196c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employee_session",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            nullable=False,
            server_default=sa.func.generate_ulid(),
        ),
        sa.Column("device_info", sa.String(), nullable=False),
        sa.Column(
            "login_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "logout_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            onupdate=sa.func.now(),
        ),
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("True"), nullable=False
        ),
        sa.ForeignKeyConstraint(["employee_id"], ["employee.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "employee_auth_track",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.func.generate_ulid(),
            nullable=False,
        ),
        sa.Column("refresh_token_id", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'ACT'"),
            nullable=False,
        ),
        sa.Column("device_info", sa.String(), nullable=False),
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
        sa.Column("employee_id", UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employee.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("refresh_token_id"),
    )


def downgrade() -> None:
    op.drop_table("employee_auth_track")
    op.drop_table("employee_session")
