"""Add deleted_at to settlement_sessions (soft delete)

Revision ID: 5b6c7d8e9f0a
Revises: 4a5b6c7d8e9f
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa

revision = '5b6c7d8e9f0a'
down_revision = '4a5b6c7d8e9f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('settlement_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('settlement_sessions', schema=None) as batch_op:
        batch_op.drop_column('deleted_at')
