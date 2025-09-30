"""merge_customer_portal_and_network_models

Revision ID: 9da0a0ad1dbd
Revises: 8e5d9a1b2c3f, 3cf0e5a563e3
Create Date: 2025-08-29 15:48:58.339544

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9da0a0ad1dbd'
down_revision: Union[str, Sequence[str], None] = ('8e5d9a1b2c3f', '3cf0e5a563e3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
