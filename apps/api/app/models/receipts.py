from datetime import date, datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base


class Receipt(Base):
    """Receipt model"""

    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,  # optional but often useful
    )

    image_path: Mapped[str] = mapped_column(String, nullable=False)  # minio://bucket/object_name

    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)

    # uploaded, processing, processed, failed
    status: Mapped[str] = mapped_column(String, nullable=False, default="uploaded")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )
