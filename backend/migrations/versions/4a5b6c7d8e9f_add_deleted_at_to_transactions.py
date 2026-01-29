"""Add deleted_at to transactions (soft delete)

Revision ID: 4a5b6c7d8e9f
Revises: 31e2876013dd
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa

revision = '4a5b6c7d8e9f'
down_revision = '31e2876013dd'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.drop_column('deleted_at')
