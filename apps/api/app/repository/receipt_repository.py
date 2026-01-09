from typing import List, Optional
from app.models.receipts import Receipt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, insert


class ReceiptRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def save(self, receipt: Receipt) -> Receipt:
        """Save a single receipt and return it"""
        self.db.add(receipt)
        await self.db.commit()
        await self.db.refresh(receipt)

        return receipt

    async def save_many(self, receipts: List[Receipt]) -> int:
        """Save multiple receipts and return the number of rows inserted"""
        self.db.add_all(receipts)
        await self.db.commit()
        
        return len(receipts)

    async def get_by_id(self, receipt_id: int) -> Receipt | None:
        result = await self.db.execute(select(Receipt).where(Receipt.id == receipt_id))

        return result.scalar_one_or_none()

    async def get_all(self, params: dict) -> List[Receipt]:

        # pagination params
        last_id: Optional[int] = params.get("last_id")
        limit: int = int(params.get("limit", 5))

        conditions = self.__get_condtions(params)

        if last_id is not None:
            conditions.append(Receipt.id > last_id)

        result = await self.db.execute(
            select(Receipt).where(and_(*conditions)).order_by(Receipt.id.asc()).limit(limit)
        )

        return list(result.scalars().all())

    def __get_condtions(self, params: dict) -> List:
        conditions = []
        if "user_id" in params:
            conditions.append(Receipt.user_id == params["user_id"])

        return conditions
