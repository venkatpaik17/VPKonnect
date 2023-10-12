"""Change the type of specific columns like status, type to Enum from String to make sure only predefined strings are used

Revision ID: 31274edd7054
Revises: 8c9e77dfe9aa
Create Date: 2023-10-09 09:53:07.131571

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "31274edd7054"
down_revision: Union[str, None] = "8c9e77dfe9aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # update the existing rows with new values
    op.execute(
        """
            UPDATE "user"
            SET status = CASE
                WHEN status = 'active' THEN 'ACT'
                WHEN status = 'inactive' THEN 'INA'
                WHEN status = 'restricted_partial' THEN 'RSP'
                WHEN status = 'restricted_full' THEN 'RSF'
                WHEN status = 'deactivated_hide' THEN 'DAH'
                WHEN status = 'deactivated_keep' THEN 'DAK'
                WHEN status = 'pending_delete_hide' THEN 'PDH'
                WHEN status = 'pending_delete_keep' THEN 'PDK'
                WHEN status = 'temporary_ban' THEN 'TBN'
                WHEN status = 'permanent_ban' THEN 'PBN'
                WHEN status = 'deleted' THEN 'DEL'
            END
        """
    )

    op.execute(
        """
            UPDATE "user"
            SET account_visibility = CASE
                WHEN account_visibility = 'public' THEN 'PBC'
                WHEN account_visibility = 'private' THEN 'PRV'
            END
        """
    )

    op.execute(
        """
            UPDATE "user"
            SET type = CASE
                WHEN type = 'standard' THEN 'STD'
                WHEN type = 'admin' THEN 'ADM'
            END
        """
    )

    op.execute(
        """
            UPDATE post
            SET status = CASE
                WHEN status = 'published' THEN 'PUB'
                WHEN status = 'draft' THEN 'DRF'
                WHEN status = 'hidden' THEN 'HID'
                WHEN status = 'banned' THEN 'BAN'
                WHEN status = 'deleted' THEN 'DEL'
            END
        """
    )

    op.execute(
        """
            UPDATE post_like
            SET status = CASE
                WHEN status = 'active' THEN 'ACT'
                WHEN status = 'hidden' THEN 'HID'
                WHEN status = 'deleted' THEN 'DEL'
            END
        """
    )

    op.execute(
        """
            UPDATE "comment"
            SET status = CASE
                WHEN status = 'published' THEN 'PUB'
                WHEN status = 'hidden' THEN 'HID'
                WHEN status = 'banned' THEN 'BAN'
                WHEN status = 'deleted' THEN 'DEL'
            END
        """
    )

    op.execute(
        """
            UPDATE comment_like
            SET status = CASE
                WHEN status = 'active' THEN 'ACT'
                WHEN status = 'hidden' THEN 'HID'
                WHEN status = 'deleted' THEN 'DEL'
            END
        """
    )

    op.execute(
        """
            UPDATE user_follow_association 
            SET status = CASE
                WHEN status='accepted' THEN 'ACP'
                WHEN status='rejected' THEN 'REJ'
                WHEN status='pending' THEN 'PND'
                WHEN status='unfollowed' THEN 'UNF'
            END
        """
    )

    op.execute(
        """
            UPDATE user_auth_track
            SET status = CASE
                WHEN status = 'active' THEN 'ACT'
                WHEN status = 'expired' THEN 'EXP'
                WHEN status = 'invalid' THEN 'INV'
            END
        """
    )

    # create enum types
    op.execute(
        "CREATE TYPE user_status_enum AS ENUM ('ACT', 'INA', 'RSP', 'RSF', 'DAH', 'DAK', 'PDH', 'PDK', 'TBN', 'PBN', 'DEL')"
    )

    op.execute("CREATE TYPE user_account_visibility_enum AS ENUM ('PBC', 'PRV')")

    op.execute("CREATE TYPE user_type_enum AS ENUM ('STD', 'ADM')")

    op.execute(
        "CREATE TYPE post_status_enum AS ENUM ('PUB', 'DRF', 'HID', 'BAN', 'DEL')"
    )

    op.execute("CREATE TYPE post_like_status_enum AS ENUM ('ACT', 'HID', 'DEL')")

    op.execute("CREATE TYPE comment_status_enum AS ENUM ('PUB', 'HID', 'BAN', 'DEL')")

    op.execute("CREATE TYPE comment_like_status_enum AS ENUM ('ACT', 'HID', 'DEL')")

    op.execute(
        "CREATE TYPE user_follow_association_status_enum AS ENUM ('ACP', 'REJ', 'PND', 'UNF')"
    )

    op.execute("CREATE TYPE user_auth_track_status_enum AS ENUM ('ACT', 'EXP', 'INV')")

    # drop the existing default value before setting new default enum value
    op.execute("""ALTER TABLE "user" ALTER status DROP DEFAULT""")

    op.execute("""ALTER TABLE "user" ALTER account_visibility DROP DEFAULT""")

    op.execute("""ALTER TABLE "user" ALTER type DROP DEFAULT""")

    op.execute("""ALTER TABLE post_like ALTER status DROP DEFAULT""")

    op.execute("""ALTER TABLE "comment" ALTER status DROP DEFAULT""")

    op.execute("""ALTER TABLE comment_like ALTER status DROP DEFAULT""")

    op.execute("""ALTER TABLE user_auth_track ALTER status DROP DEFAULT""")

    # change the types of columns to created enum types
    op.alter_column(
        "user",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.Enum(name="user_status_enum"),
        nullable=False,
        server_default=sa.text("'ACT'::user_status_enum"),
        postgresql_using="status::user_status_enum",
    )

    op.alter_column(
        "user",
        "account_visibility",
        existing_type=sa.String(length=20),
        type_=sa.Enum(name="user_account_visibility_enum"),
        nullable=False,
        server_default=sa.text("'PBC'::user_account_visibility_enum"),
        postgresql_using="account_visibility::user_account_visibility_enum",
    )

    op.alter_column(
        "user",
        "type",
        existing_type=sa.String(length=20),
        type_=sa.Enum(name="user_type_enum"),
        nullable=False,
        server_default=sa.text("'STD'::user_type_enum"),
        postgresql_using="type::user_type_enum",
    )

    op.alter_column(
        "post",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.Enum(name="post_status_enum"),
        nullable=False,
        postgresql_using="status::post_status_enum",
    )

    op.alter_column(
        "post_like",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.Enum(name="post_like_status_enum"),
        nullable=False,
        server_default=sa.text("'ACT'::post_like_status_enum"),
        postgresql_using="status::post_like_status_enum",
    )

    op.alter_column(
        "comment",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.Enum(name="comment_status_enum"),
        nullable=False,
        server_default=sa.text("'PUB'::comment_status_enum"),
        postgresql_using="status::comment_status_enum",
    )

    op.alter_column(
        "comment_like",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.Enum(name="comment_like_status_enum"),
        nullable=False,
        server_default=sa.text("'ACT'::comment_like_status_enum"),
        postgresql_using="status::comment_like_status_enum",
    )

    op.alter_column(
        "user_follow_association",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.Enum(name="user_follow_association_status_enum"),
        nullable=False,
        postgresql_using="status::user_follow_association_status_enum",
    )

    op.alter_column(
        "user_auth_track",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.Enum(name="user_auth_track_status_enum"),
        nullable=False,
        server_default=sa.text("'ACT'::user_auth_track_status_enum"),
        postgresql_using="status::user_auth_track_status_enum",
    )


def downgrade() -> None:
    # change column type back to string
    op.alter_column(
        "user_auth_track",
        "status",
        existing_type=sa.Enum(name="user_auth_track_status_enum"),
        type_=sa.String(length=20),
        nullable=False,
        server_default=sa.text("'active'"),
    )

    op.alter_column(
        "user_follow_association",
        "status",
        existing_type=sa.Enum(name="user_follow_association_status_enum"),
        type_=sa.String(length=20),
        nullable=False,
    )

    op.alter_column(
        "comment_like",
        "status",
        existing_type=sa.Enum(name="comment_like_status_enum"),
        type_=sa.String(length=20),
        nullable=False,
        server_default=sa.text("'active'"),
    )

    op.alter_column(
        "comment",
        "status",
        existing_type=sa.Enum(name="comment_status_enum"),
        type_=sa.String(length=20),
        nullable=False,
        server_default=sa.text("'published'"),
    )

    op.alter_column(
        "post_like",
        "status",
        existing_type=sa.Enum(name="post_like_status_enum"),
        type_=sa.String(length=20),
        nullable=False,
        server_default=sa.text("'active'"),
    )

    op.alter_column(
        "post",
        "status",
        existing_type=sa.Enum(name="post_status_enum"),
        type_=sa.String(length=20),
        nullable=False,
    )

    op.alter_column(
        "user",
        "type",
        existing_type=sa.Enum(name="user_type_enum"),
        type_=sa.String(length=20),
        nullable=False,
        server_default=sa.text("'standard'"),
    )

    op.alter_column(
        "user",
        "account_visibility",
        existing_type=sa.Enum(name="user_account_visibility_enum"),
        type_=sa.String(length=20),
        nullable=False,
        server_default=sa.text("'public'"),
    )

    op.alter_column(
        "user",
        "status",
        existing_type=sa.Enum(name="user_status_enum"),
        type_=sa.String(length=20),
        nullable=False,
        server_default=sa.text("'active'"),
    )

    # drop all the created enum types
    op.execute("DROP TYPE IF EXISTS user_auth_track_status_enum")

    op.execute("DROP TYPE IF EXISTS user_follow_association_status_enum")

    op.execute("DROP TYPE IF EXISTS comment_like_status_enum")

    op.execute("DROP TYPE IF EXISTS comment_status_enum")

    op.execute("DROP TYPE IF EXISTS post_like_status_enum")

    op.execute("DROP TYPE IF EXISTS post_status_enum")

    op.execute("DROP TYPE IF EXISTS user_type_enum")

    op.execute("DROP TYPE IF EXISTS user_account_visibility_enum")

    op.execute("DROP TYPE IF EXISTS user_status_enum")

    # update existing rows with old values
    op.execute(
        """
            UPDATE user_auth_track
            SET status = CASE
                WHEN status = 'ACT' THEN 'active'
                WHEN status = 'EXP' THEN 'expired'
                WHEN status = 'INV' THEN 'invalid'
            END
        """
    )

    op.execute(
        """
            UPDATE user_follow_association 
            SET status = CASE
                WHEN status='ACP' THEN 'accepted'
                WHEN status='REJ' THEN 'rejected'
                WHEN status='PND' THEN 'pending'
                WHEN status='UNF' THEN 'unfollowed'
            END
        """
    )

    op.execute(
        """
            UPDATE comment_like
            SET status = CASE
                WHEN status = 'ACT' THEN 'active'
                WHEN status = 'HID' THEN 'hidden'
                WHEN status = 'DEL' THEN 'deleted'
            END
        """
    )

    op.execute(
        """
            UPDATE "comment"
            SET status = CASE
                WHEN status = 'PUB' THEN 'published'
                WHEN status = 'HID' THEN 'hidden'
                WHEN status = 'BAN' THEN 'banned'
                WHEN status = 'DEL' THEN 'deleted'
            END
        """
    )

    op.execute(
        """
            UPDATE post_like
            SET status = CASE
                WHEN status = 'ACT' THEN 'active'
                WHEN status = 'HID' THEN 'hidden'
                WHEN status = 'DEL' THEN 'deleted'
            END
        """
    )

    op.execute(
        """
            UPDATE post
            SET status =CASE
                WHEN status = 'PUB' THEN 'published'
                WHEN status = 'DRF' THEN 'draft'
                WHEN status = 'HID' THEN 'hidden'
                WHEN status = 'BAN' THEN 'banned'
                WHEN status = 'DEL' THEN 'deleted'
            END
        """
    )

    op.execute(
        """
            UPDATE "user"
            SET type = CASE
                WHEN type = 'STD' THEN 'standard'
                WHEN type = 'ADM' THEN 'admin'
            END
        """
    )

    op.execute(
        """
            UPDATE "user"
            SET account_visibility = CASE
                WHEN account_visibility = 'PBC' THEN 'public'
                WHEN account_visibility = 'PRV' THEN 'private'
            END
        """
    )

    op.execute(
        """
            UPDATE "user" 
            SET status = CASE
                WHEN status = 'ACT' THEN 'active'
                WHEN status = 'INA' THEN 'inactive'
                WHEN status = 'RSP' THEN 'restricted_partial'
                WHEN status = 'RSF' THEN 'restricted_full'
                WHEN status = 'DAH' THEN 'deactivated_hide'
                WHEN status = 'DAK' THEN 'deactivated_keep'
                WHEN status = 'PDH' THEN 'pending_delete_hide'
                WHEN status = 'PDK' THEN 'pending_delete_keep'
                WHEN status = 'TBN' THEN 'temporary_ban'
                WHEN status = 'PBN' THEN 'permanent_ban'
                WHEN status = 'DEL' THEN 'deleted'
            END
        """
    )
