"""remove device_info from user_account_history table

Revision ID: bcab7556473a
Revises: 2ecce19d2b31
Create Date: 2024-04-02 21:43:11.474610

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bcab7556473a"
down_revision: Union[str, None] = "2ecce19d2b31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("user_account_history", "device_info")


def downgrade() -> None:
    op.add_column(
        "user_account_history", sa.Column("device_info", sa.String(), nullable=False)
    )
