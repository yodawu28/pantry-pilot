from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select, func, Column, Integer, String, Numeric, DateTime
from sqlalchemy.orm import declarative_base
from app.config import settings
from shared.types import ReceiptContext

# Create async engine for database access
engine = create_async_engine(settings.database_url, echo=False)

# Define a minimal Receipt model for MCP queries (read-only)
Base = declarative_base()

class Receipt(Base):
    """Minimal Receipt model for MCP context queries."""
    __tablename__ = "receipts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    merchant_name = Column(String(200))
    total_amount = Column(Numeric(10, 2))
    created_at = Column(DateTime)


async def get_receipt_context(receipt_id: int, user_id: int) -> ReceiptContext:
    """
    MCP Tool: Get historical context about user's receipts.
    
    Provides agent with context like:
    - How many receipts user has
    - Merchants they frequently visit
    - Average spending
    
    Args:
        receipt_id: Current receipt ID
        user_id: User ID
        
    Returns:
        ReceiptContext with historical data
    """
    async with AsyncSession(engine) as session:
        # Count total receipt
        count_result = await session.execute(
            select(func.count(Receipt.id)).where(Receipt.user_id == user_id)
        )

        total_result = count_result.scalar_one() or 0

        merchants_result = await session.execute(
            select(Receipt.merchant_name)
            .where(Receipt.user_id == user_id)
            .where(Receipt.merchant_name.isnot(None))
            .order_by(Receipt.created_at.desc())
            .limit(10)
        )

        merchants = [row[0] for row in merchants_result.fetchall() if row[0]]
        unique_merchants = list(dict.fromkeys(merchants))[:5]

        # calculate average total
        avg_result = await session.execute(
            select(func.avg(Receipt.total_amount))
            .where(Receipt.user_id == user_id)
            .where(Receipt.total_amount.isnot(None))
        )

        avg_total = avg_result.scalar_one()

        return ReceiptContext(
            receipt_id=receipt_id,
            user_id=user_id,
            previous_receipts_count=total_result,
            merchant_history=unique_merchants,
            avg_total=Decimal(str(avg_total)) if avg_total else None
        )