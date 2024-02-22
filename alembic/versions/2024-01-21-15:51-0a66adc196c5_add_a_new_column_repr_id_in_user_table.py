"""Add a new column repr_id in user table

Revision ID: 0a66adc196c5
Revises: 1259c014d835
Create Date: 2024-01-21 15:51:53.515044

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0a66adc196c5"
down_revision: Union[str, None] = "1259c014d835"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column(
            "repr_id",
            UUID(as_uuid=True),
            nullable=False,
            server_default=sa.func.gen_random_uuid(),
        ),
    )

    # populate available entries with uuid for repr_id
    op.execute('UPDATE "user" SET repr_id = gen_random_uuid()')


def downgrade() -> None:
    op.drop_column("user", "repr_id")
