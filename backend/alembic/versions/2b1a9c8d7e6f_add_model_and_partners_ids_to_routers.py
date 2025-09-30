"""Add model and partners_ids to routers

Revision ID: 2b1a9c8d7e6f
Revises: ab6c1069c5f8
Create Date: 2025-08-27 09:02:15.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b1a9c8d7e6f'
down_revision: Union[str, Sequence[str], None] = 'ab6c1069c5f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('routers', sa.Column('model', sa.String(length=255), nullable=True))
    op.add_column('routers', sa.Column('partners_ids', sa.ARRAY(sa.Integer()), nullable=False, server_default='{}'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('routers', 'partners_ids')
    op.drop_column('routers', 'model')
