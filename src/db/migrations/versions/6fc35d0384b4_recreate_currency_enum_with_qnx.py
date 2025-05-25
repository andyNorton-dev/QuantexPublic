"""recreate_currency_enum_with_qnx

Revision ID: 6fc35d0384b4
Revises: 4c1d7895f036
Create Date: 2025-04-09 12:48:23.639956

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6fc35d0384b4'
down_revision: Union[str, None] = '4c1d7895f036'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
