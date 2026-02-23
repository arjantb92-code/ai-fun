"""add receipt_url to transactions

Revision ID: d5e6f7a8b9c0
Revises: cf10bff0b1f2
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "d5e6f7a8b9c0"
down_revision = "cf10bff0b1f2"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if "receipt_url" not in [c["name"] for c in inspect(conn).get_columns("transactions")]:
        op.add_column("transactions", sa.Column("receipt_url", sa.String(255), nullable=True))


def downgrade():
    op.drop_column("transactions", "receipt_url")
