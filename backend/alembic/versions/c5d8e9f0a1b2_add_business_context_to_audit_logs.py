"""Add business_context to audit_logs

Revision ID: c5d8e9f0a1b2
Revises: 2b1a9c8d7e6f
Create Date: 2025-08-27 09:33:15.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5d8e9f0a1b2'
down_revision: Union[str, Sequence[str], None] = '2b1a9c8d7e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('audit_logs', sa.Column('business_context', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('audit_logs', 'business_context')