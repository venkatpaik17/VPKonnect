"""Make case_number in user_content_report_detail as unique

Revision ID: e490e8766791
Revises: 78b50efef30c
Create Date: 2024-02-06 15:57:51.772855

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e490e8766791"
down_revision: Union[str, None] = "78b50efef30c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "user_content_report_detail_case_number_key",
        "user_content_report_detail",
        ["case_number"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "user_content_report_detail_case_number_key",
        "user_content_report_detail",
        type_="unique",
    )
