"""Add OAuth and activation fields to users

Revision ID: 8e9f0a1b2c3d
Revises: a4cc88fc7669
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8e9f0a1b2c3d'
down_revision = 'a4cc88fc7669'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('oauth_provider', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('oauth_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('users', sa.Column('activation_token', sa.String(64), nullable=True))
    op.add_column('users', sa.Column('activation_token_expires', sa.DateTime(), nullable=True))
    
    # Create index for OAuth lookups
    op.create_index('ix_users_oauth', 'users', ['oauth_provider', 'oauth_id'])


def downgrade():
    op.drop_index('ix_users_oauth', table_name='users')
    op.drop_column('users', 'activation_token_expires')
    op.drop_column('users', 'activation_token')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'oauth_id')
    op.drop_column('users', 'oauth_provider')
