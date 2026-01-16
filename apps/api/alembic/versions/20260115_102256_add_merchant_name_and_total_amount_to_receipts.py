"""add ocr fields and receipt items

Revision ID: 002_add_ocr_fields
Revises: 001_initial_schema
Create Date: 2026-01-15 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002_add_ocr_fields"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    # Add OCR fields to receipts table (purchase_date already exists from initial schema)
    op.add_column("receipts", sa.Column("merchant_name", sa.String(200), nullable=True))
    op.add_column("receipts", sa.Column("total_amount", sa.Numeric(10, 2), nullable=True))
    op.add_column("receipts", sa.Column("currency", sa.String(3), server_default="USD"))
    op.add_column(
        "receipts", sa.Column("ocr_status", sa.String(20), server_default="pending", nullable=False)
    )
    op.add_column("receipts", sa.Column("ocr_text", sa.Text(), nullable=True))
    op.add_column("receipts", sa.Column("parsed_at", sa.DateTime(), nullable=True))
    op.add_column("receipts", sa.Column("extraction_confidence", sa.Numeric(3, 2), nullable=True))
    op.add_column("receipts", sa.Column("extraction_errors", sa.Text(), nullable=True))

    # Add indexes
    op.create_index("ix_receipts_merchant_name", "receipts", ["merchant_name"])
    op.create_index("ix_receipts_ocr_status", "receipts", ["ocr_status"])

    # Create receipt_items table
    op.create_table(
        "receipt_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("receipt_id", sa.Integer(), nullable=False),
        sa.Column("item_name", sa.String(200), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("total_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["receipt_id"], ["receipts.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_receipt_items_receipt_id", "receipt_items", ["receipt_id"])


def downgrade():
    # Drop receipt_items table
    op.drop_index("ix_receipt_items_receipt_id", "receipt_items")
    op.drop_table("receipt_items")

    # Drop indexes from receipts
    op.drop_index("ix_receipts_ocr_status", "receipts")
    op.drop_index("ix_receipts_merchant_name", "receipts")

    # Drop columns from receipts (purchase_date was in initial schema, don't drop)
    op.drop_column("receipts", "extraction_errors")
    op.drop_column("receipts", "extraction_confidence")
    op.drop_column("receipts", "parsed_at")
    op.drop_column("receipts", "ocr_text")
    op.drop_column("receipts", "ocr_status")
    op.drop_column("receipts", "currency")
    op.drop_column("receipts", "total_amount")
    op.drop_column("receipts", "merchant_name")
