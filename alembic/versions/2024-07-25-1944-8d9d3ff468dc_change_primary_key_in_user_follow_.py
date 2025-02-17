"""change primary key in user_follow_association, post_like and comment_like and create a unique key

Revision ID: 8d9d3ff468dc
Revises: 429fe181bd71
Create Date: 2024-07-25 19:44:37.966946

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8d9d3ff468dc"
down_revision: Union[str, None] = "429fe181bd71"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # user_follow_association
    # drop old primary keys
    op.drop_constraint(
        "user_follow_association_pkey", "user_follow_association", type_="primary"
    )

    # set new primary keys
    op.create_primary_key(
        "user_follow_association_pkey",
        "user_follow_association",
        ["id"],
    )

    op.create_unique_constraint(
        "user_follow_association_follower_followed_status_created_at_key",
        "user_follow_association",
        ["follower_user_id", "followed_user_id", "status", "created_at"],
    )

    # post_like
    # drop old primary keys
    op.drop_constraint("post_like_pkey", "post_like", type_="primary")

    # set new primary keys
    op.create_primary_key(
        "post_like_pkey",
        "post_like",
        ["id"],
    )

    # drop unique constraint
    op.drop_constraint("post_like_id_key", "post_like", type_="unique")

    op.create_unique_constraint(
        "post_like_post_id_user_id_status_created_at_key",
        "post_like",
        ["post_id", "user_id", "status", "created_at"],
    )

    # comment_like
    # drop old primary keys
    op.drop_constraint("comment_like_pkey", "comment_like", type_="primary")

    # set new primary keys
    op.create_primary_key(
        "comment_like_pkey",
        "comment_like",
        ["id"],
    )

    # drop unique constraint
    op.drop_constraint("comment_like_id_key", "comment_like", type_="unique")

    op.create_unique_constraint(
        "comment_like_comment_id_user_id_status_created_at_key",
        "comment_like",
        ["comment_id", "user_id", "status", "created_at"],
    )


def downgrade() -> None:
    # comment_like
    op.drop_constraint(
        "comment_like_comment_id_user_id_status_created_at_key",
        "comment_like",
        type_="unique",
    )
    op.create_unique_constraint(
        "comment_like_id_key",
        "comment_like",
        ["id"],
    )
    op.drop_constraint("comment_like_pkey", "comment_like", type_="primary")
    op.create_primary_key(
        "comment_like_pkey",
        "comment_like",
        ["user_id", "comment_id"],
    )

    # post_like
    op.drop_constraint(
        "post_like_post_id_user_id_status_created_at_key",
        "post_like",
        type_="unique",
    )
    op.create_unique_constraint(
        "post_like_id_key",
        "post_like",
        ["id"],
    )
    op.drop_constraint("post_like_pkey", "post_like", type_="primary")
    op.create_primary_key(
        "post_like_pkey",
        "post_like",
        ["user_id", "post_id"],
    )

    # user_follow_association
    op.drop_constraint(
        "user_follow_association_follower_followed_status_created_at_key",
        "user_follow_association",
        type_="unique",
    )
    op.drop_constraint(
        "user_follow_association_pkey", "user_follow_association", type_="primary"
    )
    op.create_primary_key(
        "user_follow_association_pkey",
        "user_follow_association",
        ["id", "follower_user_id", "followed_user_id"],
    )
