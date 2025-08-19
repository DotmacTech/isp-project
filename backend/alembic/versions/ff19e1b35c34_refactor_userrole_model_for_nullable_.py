"""Refactor UserRole model for nullable scope

Revision ID: ff19e1b35c34
Revises: bbd2673cc84e
Create Date: 2025-08-15 14:53:47.916398

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff19e1b35c34'
down_revision: Union[str, Sequence[str], None] = 'bbd2673cc84e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Manually drop the existing primary key
    op.drop_constraint('user_roles_pkey', 'user_roles', type_='primary')

    # Alter columns to be nullable
    op.alter_column('user_roles', 'customer_id', existing_type=sa.BIGINT(), nullable=True)
    op.alter_column('user_roles', 'reseller_id', existing_type=sa.BIGINT(), nullable=True)

    # Create new primary key on id
    op.create_primary_key('user_roles_pkey', 'user_roles', ['id'])

    op.create_index('ix_user_roles_id', 'user_roles', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_user_roles_id', table_name='user_roles')
    op.drop_constraint('_user_role_scope_uc', 'user_roles', type_='unique')
    op.drop_constraint('user_roles_pkey', 'user_roles', type_='primary')

    op.drop_column('user_roles', 'id')

    op.alter_column('user_roles', 'reseller_id', existing_type=sa.BIGINT(), nullable=False)
    op.alter_column('user_roles', 'customer_id', existing_type=sa.BIGINT(), nullable=False)

    # Recreate the old primary key
    op.create_primary_key(
        'user_roles_pkey',
        'user_roles',
        ['user_id', 'role_id', 'customer_id', 'reseller_id']
    )