"""Create a view for the join of user_content_restrict_ban_appeal_detail and user_restrict_ban_detail tables

Revision ID: 5bd88146bc48
Revises: 19907c61d687
Create Date: 2024-03-02 10:35:18.422686

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5bd88146bc48"
down_revision: Union[str, None] = "19907c61d687"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
            CREATE VIEW appeal_restrict_join_view AS
            SELECT ROW_NUMBER() OVER() AS id,
                a.user_id,
                a.report_id,
                a.content_type AS "appeal_content_type",
                a.content_id AS "appeal_content_id",
                a.status AS "appeal_status",
                r.status AS "user_restrict_ban_status",
                r.duration AS "user_restrict_ban_duration",
                r.is_deleted AS "user_restrict_ban_is_deleted",
                r.is_active AS "user_restrict_ban_is_active",
                r.content_type AS "user_restrict_ban_content_type",
                r.content_id AS "user_restrict_ban_content_id"
            FROM user_content_restrict_ban_appeal_detail AS a
            LEFT JOIN user_restrict_ban_detail AS r ON a.report_id = r.report_id
            WHERE a.status = 'ACP';
        """
    )


def downgrade() -> None:
    op.execute(
        """
            DROP VIEW appeal_restrict_join_view;
        """
    )
