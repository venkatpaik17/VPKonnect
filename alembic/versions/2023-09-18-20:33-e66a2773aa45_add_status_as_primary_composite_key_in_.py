"""add status as primary/composite key in user_follow_association table

Revision ID: e66a2773aa45
Revises: 
Create Date: 2023-09-18 20:33:10.891176

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e66a2773aa45"
down_revision: Union[str, None] = None
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
