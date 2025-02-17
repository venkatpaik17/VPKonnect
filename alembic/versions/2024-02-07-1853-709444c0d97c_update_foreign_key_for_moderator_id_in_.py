"""Update foreign key for moderator_id in user_content_report_detail from user to employee

Revision ID: 709444c0d97c
Revises: e490e8766791
Create Date: 2024-02-07 18:53:40.531098

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "709444c0d97c"
down_revision: Union[str, None] = "e490e8766791"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "user_content_report_detail_moderator_id_fkey",
        "user_content_report_detail",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "user_content_report_detail_moderator_id_fkey",
        "user_content_report_detail",
        "employee",
        ["moderator_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "user_content_report_detail_moderator_id_fkey",
        "user_content_report_detail",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "user_content_report_detail_moderator_id_fkey",
        "user_content_report_detail",
        "user",
        ["moderator_id"],
        ["id"],
        ondelete="CASCADE",
    )
