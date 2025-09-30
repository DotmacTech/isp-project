"""recreate nas table for freeradius compatibility

Revision ID: 1a2b3c4d5e6f
Revises: 82f90642c54c
Create Date: 2025-09-15 11:10:21.359123

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a2b3c4d5e6f'
down_revision: Union[str, None] = '82f90642c54c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Recreate the nas table for FreeRADIUS compatibility."""
    # First, drop the existing 'nas' table to ensure the 'create' operation can succeed.
    # This is necessary because the table might exist from a previous state or manual creation.
    op.drop_table('nas')
    op.create_table('nas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nasname', sa.String(length=128), nullable=False),
        sa.Column('shortname', sa.String(length=32), nullable=False),
        sa.Column('type', sa.String(length=30), server_default='other', nullable=False),
        sa.Column('ports', sa.Integer(), nullable=True),
        sa.Column('secret', sa.String(length=60), nullable=False),
        sa.Column('server', sa.String(length=64), nullable=True),
        sa.Column('community', sa.String(length=50), nullable=True),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('nas_nasname_idx', 'nas', ['nasname'], unique=False)
    op.create_index('nas_shortname_idx', 'nas', ['shortname'], unique=True)


def downgrade() -> None:
    """Remove the nas table."""
    op.drop_table('nas')