"""Merge receipt_url and oauth/activation heads

Revision ID: e7f8a9b0c1d2
Revises: d5e6f7a8b9c0, 8e9f0a1b2c3d
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa


revision = 'e7f8a9b0c1d2'
down_revision = ('d5e6f7a8b9c0', '8e9f0a1b2c3d')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
