"""Change image type from LargeBinary to String in post table, storing filename instead of image

Revision ID: 60fe7fae86c7
Revises: 5b7b4d6c3267
Create Date: 2023-10-30 10:32:43.555969

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "60fe7fae86c7"
down_revision: Union[str, None] = "5b7b4d6c3267"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "post",
        "image",
        existing_type=sa.LargeBinary(length=20971520),
        type_=sa.String(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "post",
        "image",
        existing_type=sa.String(),
        type_=sa.LargeBinary(length=20971520),
        nullable=False,
        postgresql_using="image::bytea",
    )
