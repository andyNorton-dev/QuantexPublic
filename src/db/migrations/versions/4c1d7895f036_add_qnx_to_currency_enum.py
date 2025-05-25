"""add_qnx_to_currency_enum

Revision ID: 4c1d7895f036
Revises: 3e74838e4f81
Create Date: 2025-04-09 12:47:15.704668

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c1d7895f036'
down_revision: Union[str, None] = '3e74838e4f81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
