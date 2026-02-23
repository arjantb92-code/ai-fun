"""Add balance_lists and balance_list_members tables

Revision ID: 7d8e9f0a1b2c
Revises: 5b6c7d8e9f0a
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7d8e9f0a1b2c'
down_revision = '5b6c7d8e9f0a'
branch_labels = None
depends_on = None


def upgrade():
    # Create balance_lists table
    op.create_table(
        'balance_lists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True, server_default='EUR'),
        sa.Column('invite_code', sa.String(length=32), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invite_code')
    )
    
    # Create balance_list_members table
    op.create_table(
        'balance_list_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('balance_list_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=True, server_default='member'),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['balance_list_id'], ['balance_lists.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('balance_list_id', 'user_id', name='unique_membership')
    )
    
    # Add balance_list_id to trips
    op.add_column('trips', sa.Column('balance_list_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_trips_balance_list', 'trips', 'balance_lists', ['balance_list_id'], ['id'])
    
    # Add balance_list_id to transactions
    op.add_column('transactions', sa.Column('balance_list_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_transactions_balance_list', 'transactions', 'balance_lists', ['balance_list_id'], ['id'])
    
    # Add balance_list_id to settlement_sessions
    op.add_column('settlement_sessions', sa.Column('balance_list_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_settlement_sessions_balance_list', 'settlement_sessions', 'balance_lists', ['balance_list_id'], ['id'])


def downgrade():
    # Remove foreign keys first
    op.drop_constraint('fk_settlement_sessions_balance_list', 'settlement_sessions', type_='foreignkey')
    op.drop_column('settlement_sessions', 'balance_list_id')
    
    op.drop_constraint('fk_transactions_balance_list', 'transactions', type_='foreignkey')
    op.drop_column('transactions', 'balance_list_id')
    
    op.drop_constraint('fk_trips_balance_list', 'trips', type_='foreignkey')
    op.drop_column('trips', 'balance_list_id')
    
    # Drop tables
    op.drop_table('balance_list_members')
    op.drop_table('balance_lists')
