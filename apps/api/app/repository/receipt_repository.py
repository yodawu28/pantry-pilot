from typing import List, Optional
from app.models.receipts import Receipt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload


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

    async def get_by_id_with_items(self, receipt_id: int) -> Receipt | None:
        """Get receipt by ID with line items loaded"""
        result = await self.db.execute(
            select(Receipt).options(selectinload(Receipt.items)).where(Receipt.id == receipt_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, params: dict = {}) -> List[Receipt]:

        # pagination params
        last_id: Optional[int] = params.get("last_id")
        limit: int = int(params.get("limit", 5))

        conditions = self.__get_conditions(params)

        order_by = self.__get_order_by(params)

        # Only add last_id filter if it's a positive value
        if last_id is not None and last_id > 0:
            conditions.append(Receipt.id < last_id)

        result = await self.db.execute(
            select(Receipt).where(and_(*conditions)).order_by(order_by).limit(limit)
        )

        return list(result.scalars().all())

    async def count(self, params: dict = {}) -> int:
        conditions = self.__get_conditions(params)

        result = await self.db.execute(
            select(func.count()).select_from(Receipt).where(and_(*conditions))
        )

        return result.scalar_one()

    async def update_status(
        self, receipt_id: int, status: Optional[str] = None, ocr_status: Optional[str] = None
    ) -> bool:
        """Update receipt status and/or ocr_status."""
        receipt = await self.get_by_id(receipt_id)
        if not receipt:
            return False

        if status:
            receipt.status = status
        if ocr_status:
            receipt.ocr_status = ocr_status

        await self.db.commit()
        return True

    def __get_conditions(self, params: dict) -> List:
        conditions = []
        if "user_id" in params:
            conditions.append(Receipt.user_id == params["user_id"])
        if "ocr_status" in params:
            conditions.append(Receipt.ocr_status == params["ocr_status"])

        return conditions

    def __get_order_by(self, params: dict):
        order_by: str = str(params.get("order_by"))
        order_direction = str(params.get("direction"))

        order = Receipt.id

        if order_by == "created_at":
            order = Receipt.created_at

        if order_direction == "asc":
            return order.asc()

        return order.desc()
