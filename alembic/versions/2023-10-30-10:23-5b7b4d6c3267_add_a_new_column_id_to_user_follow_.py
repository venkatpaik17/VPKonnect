"""Add a new column 'id' to user_follow_association table and change the primary key to [id, follower_user_id, followed_user_id]

Revision ID: 5b7b4d6c3267
Revises: 0755ddd27255
Create Date: 2023-10-30 10:23:06.829570

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5b7b4d6c3267"
down_revision: Union[str, None] = "0755ddd27255"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # create a new column 'id'
    op.add_column(
        "user_follow_association",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            nullable=False,
            server_default=sa.func.generate_ulid(),
        ),
    )

    # update new column with values for already existing rows
    op.execute("UPDATE user_follow_association SET id = generate_ulid()")

    # drop old primary keys
    op.drop_constraint(
        "user_follow_association_pkey", "user_follow_association", type_="primary"
    )

    # set new primary keys
    op.create_primary_key(
        "user_follow_association_pkey",
        "user_follow_association",
        ["id", "follower_user_id", "followed_user_id"],
    )


def downgrade() -> None:
    # drop newly created primary keys
    op.drop_constraint(
        "user_follow_association_pkey", "user_follow_association", type_="primary"
    )

    # revert to previous primary keys
    op.create_primary_key(
        "user_follow_association_pkey",
        "user_follow_association",
        ["status", "follower_user_id", "followed_user_id"],
    )

    # remove the column
    op.drop_column("user_follow_association", "id")
