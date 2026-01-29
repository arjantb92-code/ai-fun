"""add category to transactions

Revision ID: 6c7d8e9f0a1b
Revises: 5b6c7d8e9f0a_add_deleted_at_to_settlement_sessions
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c7d8e9f0a1b'
down_revision = '5b6c7d8e9f0a_add_deleted_at_to_settlement_sessions'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('transactions', sa.Column('category', sa.String(50), nullable=True, server_default='overig'))


def downgrade():
    op.drop_column('transactions', 'category')
