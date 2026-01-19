from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base

if TYPE_CHECKING:
    from app.models.receipts import Receipt


class ReceiptItem(Base):
    """Individual line items from receipts."""

    __tablename__ = "receipt_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    receipt_id: Mapped[int] = mapped_column(
        ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Item details
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), default=1.0, nullable=False
    )  # Changed to Numeric to support 0.246
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(5), default="VND", nullable=False
    )  # Currency for this item

    # Extraction metadata
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)  # 0.00-1.00

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

    # Relationships
    receipt: Mapped["Receipt"] = relationship("Receipt", back_populates="items")

    def __repr__(self):
        return f"<ReceiptItem(id={self.id}, name={self.item_name}, price={self.total_price})>"
