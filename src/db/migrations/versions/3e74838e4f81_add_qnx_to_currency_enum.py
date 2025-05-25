"""add_qnx_to_currency_enum

Revision ID: 3e74838e4f81
Revises: 98cb6df8720b
Create Date: 2025-04-09 12:46:06.319708

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e74838e4f81'
down_revision: Union[str, None] = '98cb6df8720b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
