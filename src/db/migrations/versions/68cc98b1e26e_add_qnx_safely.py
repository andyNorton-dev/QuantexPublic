"""add_qnx_safely

Revision ID: 68cc98b1e26e
Revises: 6fc35d0384b4
Create Date: 2025-04-09 12:50:05.937593

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68cc98b1e26e'
down_revision: Union[str, None] = '6fc35d0384b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
