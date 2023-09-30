"""Change image type from LargeBinary to String in post table, storing filename instead of image

Revision ID: 1a5bffe2cc9e
Revises: bc55cfc696f3
Create Date: 2023-09-26 22:14:24.612092

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1a5bffe2cc9e"
down_revision: Union[str, None] = "bc55cfc696f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("post", "image", type_=sa.String(), nullable=False)


def downgrade() -> None:
    op.alter_column(
        "post", "image", type_=sa.LargeBinary(length=20971520), nullable=False
    )
