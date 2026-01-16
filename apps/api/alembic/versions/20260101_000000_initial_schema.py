"""initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-01-01 00:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Users table already exists via SQLAlchemy create_all
    # Receipts table already exists via SQLAlchemy create_all
    # This migration is a baseline - no changes needed
    pass


def downgrade():
    # Cannot downgrade from initial - would drop all tables
    pass
