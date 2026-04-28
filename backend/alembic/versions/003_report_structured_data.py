"""add structured report payload

Revision ID: 003
Revises: 002
Create Date: 2026-04-27

"""

from alembic import op
import sqlalchemy as sa


revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("structured_data_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("reports", "structured_data_json")
