"""add status as primary/composite key in user_follow_association table

Revision ID: 0755ddd27255
Revises: 782d45a772fc
Create Date: 2023-10-30 10:22:09.663528

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0755ddd27255"
down_revision: Union[str, None] = "782d45a772fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # drop the initial set primary keys
    op.drop_constraint(
        "user_follow_association_pkey", "user_follow_association", type_="primary"
    )
    # create new primary keys
    op.create_primary_key(
        "user_follow_association_pkey",
        "user_follow_association",
        ["follower_user_id", "followed_user_id", "status"],
    )


def downgrade() -> None:
    # drop the newly created primary key
    op.drop_constraint(
        "user_follow_association_pkey", "user_follow_association", type_="primary"
    )
    # revert to previous primary keys
    op.create_primary_key(
        "user_follow_association_pkey",
        "user_follow_association",
        ["follower_user_id", "followed_user_id"],
    )
