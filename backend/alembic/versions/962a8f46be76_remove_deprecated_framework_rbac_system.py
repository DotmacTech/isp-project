"""Remove deprecated framework RBAC system

Revision ID: 962a8f46be76
Revises: a1b2c3d4e5f6
Create Date: 2025-08-21 10:06:02.474393

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '962a8f46be76'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Corrected upgrade to remove only the deprecated framework RBAC system."""
    # Drop the old framework RBAC tables first
    op.drop_table('framework_role_permissions')

    with op.batch_alter_table('framework_roles', schema=None) as batch_op:
        batch_op.drop_index('ix_framework_roles_name', if_exists=True)
        batch_op.drop_index('ix_framework_roles_id', if_exists=True)
    op.drop_table('framework_roles')

    with op.batch_alter_table('framework_permissions', schema=None) as batch_op:
        batch_op.drop_index('ix_framework_permissions_code', if_exists=True)
        batch_op.drop_index('ix_framework_permissions_id', if_exists=True)
    op.drop_table('framework_permissions')

    # Remove the deprecated columns from the administrators table
    with op.batch_alter_table('administrators', schema=None) as batch_op:
        batch_op.drop_column('role')
        batch_op.drop_column('framework_roles')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Corrected downgrade to restore the deprecated framework RBAC system."""
    # Re-add the deprecated columns to the administrators table
    with op.batch_alter_table('administrators', schema=None) as batch_op:
        batch_op.add_column(sa.Column('framework_roles', postgresql.ARRAY(sa.INTEGER()), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('role', sa.VARCHAR(), autoincrement=False, nullable=True))

    # Re-create the framework_permissions table
    op.create_table('framework_permissions',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('code', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('module', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('is_system', sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint('id', name='framework_permissions_pkey')
    )
    op.create_index('ix_framework_permissions_id', 'framework_permissions', ['id'], unique=False)
    op.create_index('ix_framework_permissions_code', 'framework_permissions', ['code'], unique=True)

    # Re-create the framework_roles table
    op.create_table('framework_roles',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('is_system', sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint('id', name='framework_roles_pkey')
    )
    op.create_index('ix_framework_roles_name', 'framework_roles', ['name'], unique=True)
    op.create_index('ix_framework_roles_id', 'framework_roles', ['id'], unique=False)

    # Re-create the association table
    op.create_table('framework_role_permissions',
        sa.Column('role_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('permission_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['permission_id'], ['framework_permissions.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['framework_roles.id'], )
    )
    # ### end Alembic commands ###
