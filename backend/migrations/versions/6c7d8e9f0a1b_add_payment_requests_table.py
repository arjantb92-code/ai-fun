"""Add payment_requests table for Tikkie/iDEAL integration

Revision ID: 6c7d8e9f0a1b
Revises: 5b6c7d8e9f0a
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa

revision = '6c7d8e9f0a1b'
down_revision = '5b6c7d8e9f0a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('payment_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('settlement_id', sa.Integer(), nullable=False),
        sa.Column('tikkie_token', sa.String(length=100), nullable=False),
        sa.Column('tikkie_url', sa.String(length=500), nullable=False),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('payer_name', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['settlement_id'], ['historical_settlements.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tikkie_token')
    )


def downgrade():
    op.drop_table('payment_requests')
