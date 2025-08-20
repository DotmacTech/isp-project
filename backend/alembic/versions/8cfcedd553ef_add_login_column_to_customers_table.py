"""add login column to customers table

Revision ID: 8cfcedd553ef
Revises: ff19e1b35c34
Create Date: 2025-08-19 16:13:35.131216

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8cfcedd553ef'
down_revision: Union[str, Sequence[str], None] = 'ff19e1b35c34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # This migration adds the 'login' column to the 'customers' table.
    # The original auto-generated migration was incorrect and attempted to drop all tables.
    # This corrected version performs the intended operation.
    op.add_column('customers', sa.Column('login', postgresql.CITEXT(), nullable=True))
    op.create_unique_constraint('uq_customers_login', 'customers', ['login'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # This is the reverse operation of the upgrade.
    op.drop_constraint('uq_customers_login', 'customers', type_='unique')
    op.drop_column('customers', 'login')
    # ### end Alembic commands ###
