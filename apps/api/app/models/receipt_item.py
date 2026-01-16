from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ReceiptItem(Base):
    """Individual line items from receipts."""
    __tablename__ = "receipt_items"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey(
        "receipts.id", ondelete="CASCADE"), nullable=False, index=True)

    # Item details
    item_name = Column(String(200), nullable=False)
    quantity = Column(Numeric(10, 3), default=1.0, nullable=False)  # Changed to Numeric to support 0.246
    unit_price = Column(Numeric(10, 2), nullable=True)
    total_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(5), default="VND", nullable=False)  # Currency for this item

    # Extraction metadata
    confidence = Column(Numeric(3, 2), nullable=True)  # 0.00-1.00

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )

    def __repr__(self):
        return f"<ReceiptItem(id={self.id}, name={self.item_name}, price={self.total_price})>"
