"""Add a new column 'is_verified' to user table, change/update server defaults with updates strings, change string lengths, create a new table user_verification_code_token, copy existing data from user_password_reset_token to this new table, delete user_password_reset_token table

Revision ID: 34044c848904
Revises: 2628aa36e527
Create Date: 2023-10-30 10:37:24.236365

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "34044c848904"
down_revision: Union[str, None] = "2628aa36e527"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # new column is_verified
    op.add_column(
        "user",
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="False"),
    )

    # exisitng rows will have true
    op.execute(
        """
               UPDATE "user" SET is_verified = TRUE
        """
    )

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

    # change string lengths and update defaults with new values (enums) wherever required
    op.alter_column(
        "user",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.String(length=3),
        server_default=sa.text("'INA'"),
    )
    op.alter_column(
        "user",
        "account_visibility",
        existing_type=sa.String(length=20),
        type_=sa.String(length=3),
        server_default=sa.text("'PBC'"),
    )
    op.alter_column(
        "user",
        "type",
        existing_type=sa.String(length=20),
        type_=sa.String(length=3),
        server_default=sa.text("'STD'"),
    )
    op.alter_column(
        "post",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.String(length=3),
    )
    op.alter_column(
        "post_like",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.String(length=3),
        server_default=sa.text("'ACT'"),
    )
    op.alter_column(
        "comment",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.String(length=3),
        server_default=sa.text("'PUB'"),
    )
    op.alter_column(
        "comment_like",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.String(length=3),
        server_default=sa.text("'ACT'"),
    )
    op.alter_column(
        "user_follow_association",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.String(length=3),
    )
    op.alter_column(
        "user_auth_track",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.String(length=3),
        server_default=sa.text("'ACT'"),
    )

    # create user_verification_code_token table
    op.create_table(
        "user_verification_code_token",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            unique=True,
            nullable=False,
            server_default=sa.func.generate_ulid(),
        ),
        sa.Column("code_token_id", sa.String(), primary_key=True),
        sa.Column(
            "type",
            sa.String(length=3),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="False"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # copy existing rows from user_password_reset_token
    op.execute(
        """
            INSERT INTO user_verification_code_token (id, code_token_id, type, user_id, is_deleted, created_at)
            SELECT id, reset_token_id, 'PWR', user_id, is_deleted, created_at
            FROM user_password_reset_token
        """
    )

    op.drop_table("user_password_reset_token")


def downgrade() -> None:
    # create user_reset_password_token table
    op.create_table(
        "user_password_reset_token",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            unique=True,
            nullable=False,
            server_default=sa.func.generate_ulid(),
        ),
        sa.Column("reset_token_id", sa.String, primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="False"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # copy rows from user_verification_code_token
    op.execute(
        """
            INSERT INTO user_password_reset_token (id, reset_token_id, user_id, is_deleted, created_at)
            SELECT id, code_token_id, user_id, is_deleted, created_at
            FROM user_verification_code_token
        """
    )

    op.drop_table("user_verification_code_token")

    # change back to earlier defaults and string lengths
    op.alter_column(
        "user_auth_track",
        "status",
        existing_type=sa.String(length=3),
        type_=sa.String(length=20),
        server_default=sa.text("'active'"),
    )
    op.alter_column(
        "user_follow_association",
        "status",
        existing_type=sa.String(length=3),
        type_=sa.String(length=20),
    )
    op.alter_column(
        "comment_like",
        "status",
        existing_type=sa.String(length=3),
        type_=sa.String(length=20),
        server_default=sa.text("'active'"),
    )
    op.alter_column(
        "comment",
        "status",
        existing_type=sa.String(length=3),
        type_=sa.String(length=20),
        server_default=sa.text("'published'"),
    )
    op.alter_column(
        "post_like",
        "status",
        existing_type=sa.String(length=3),
        type_=sa.String(length=20),
        server_default=sa.text("'active'"),
    )
    op.alter_column(
        "post",
        "status",
        existing_type=sa.String(length=3),
        type_=sa.String(length=20),
    )
    op.alter_column(
        "user",
        "type",
        existing_type=sa.String(length=3),
        type_=sa.String(length=20),
        server_default=sa.text("'standard'"),
    )
    op.alter_column(
        "user",
        "account_visibility",
        existing_type=sa.String(length=3),
        type_=sa.String(length=20),
        server_default=sa.text("'public'"),
    )
    op.alter_column(
        "user",
        "status",
        existing_type=sa.String(length=3),
        type_=sa.String(length=20),
        server_default=sa.text("'active'"),
    )

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

    # drop is_verified column
    op.drop_column("user", "is_verified")
