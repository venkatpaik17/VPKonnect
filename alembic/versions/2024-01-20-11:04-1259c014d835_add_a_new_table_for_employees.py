"""Add a new table for employees

Revision ID: 1259c014d835
Revises: 99c8a0d44d36
Create Date: 2024-01-20 11:04:45.939660

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1259c014d835"
down_revision: Union[str, None] = "99c8a0d44d36"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employee",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            nullable=False,
            server_default=sa.func.generate_ulid(),
        ),
        sa.Column("emp_id", sa.String(length=16), nullable=False),
        sa.Column("first_name", sa.String(length=50), nullable=False),
        sa.Column("last_name", sa.String(length=50), nullable=False),
        sa.Column("password", sa.String(length=65), nullable=False),
        sa.Column("personal_email", sa.String(length=320), nullable=False),
        sa.Column("work_email", sa.String(length=320), nullable=False),
        sa.Column("country_phone_code", sa.String(length=10), nullable=False),
        sa.Column("phone_number", sa.String(length=12), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("profile_picture", sa.String(), nullable=True),
        sa.Column("gender", sa.String(length=1), nullable=False),
        sa.Column("aadhaar", sa.String(length=12), nullable=False),
        sa.Column("pan", sa.String(length=10), nullable=False),
        sa.Column("address_line_1", sa.Text(), nullable=False),
        sa.Column("address_line_2", sa.Text(), nullable=True),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column("state_province", sa.String(), nullable=False),
        sa.Column("zip_postal_code", sa.String(length=16), nullable=False),
        sa.Column("country", sa.String(length=3), nullable=False),
        sa.Column("join_date", sa.Date(), nullable=False),
        sa.Column("termination_date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=3),
            nullable=False,
            server_default=sa.text("'ACP'"),
        ),
        sa.Column("type", sa.String(length=3), nullable=False),
        sa.Column("designation", sa.String(length=10), nullable=False),
        sa.Column("supervisor_id", UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="False", nullable=False),
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
        sa.ForeignKeyConstraint(["supervisor_id"], ["employee.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("personal_email"),
        sa.UniqueConstraint("work_email"),
        sa.UniqueConstraint("emp_id"),
        sa.UniqueConstraint("aadhaar"),
        sa.UniqueConstraint("pan"),
    )


def downgrade() -> None:
    op.drop_table("employee")
