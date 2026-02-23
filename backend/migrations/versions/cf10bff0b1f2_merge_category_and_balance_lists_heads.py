"""merge category and balance_lists heads

Revision ID: cf10bff0b1f2
Revises: 6c7d8e9f0a1b, 7d8e9f0a1b2c
Create Date: 2026-02-23 16:06:29.888427

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cf10bff0b1f2'
down_revision = ('6c7d8e9f0a1b', '7d8e9f0a1b2c')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
