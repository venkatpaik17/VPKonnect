"""Change the type of column 'type' in user_verification_code_token table from string to enum

Revision ID: 15f5926f97fa
Revises: 6d234f8fc322
Create Date: 2023-10-14 18:58:29.477767

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "15f5926f97fa"
down_revision: Union[str, None] = "6d234f8fc322"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE user_verification_code_token_type_enum AS ENUM('PWR', 'USV', 'BNV')"
    )

    op.alter_column(
        "user_verification_code_token",
        "type",
        existing_type=sa.String,
        type_=sa.Enum(name="user_verification_code_token_type_enum"),
        nullable=False,
        postgresql_using="type::user_verification_code_token_type_enum",
    )


def downgrade() -> None:
    op.alter_column(
        "user_verification_code_token",
        "type",
        existing_type=sa.Enum(name="user_verification_code_token_type_enum"),
        type_=sa.String,
        nullable=False,
    )

    op.execute("DROP TYPE IF EXISTS user_verification_code_token_type_enum")
