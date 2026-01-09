from datetime import date
import sys
from typing import List
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.receipt_repository import ReceiptRepository
from app.services.minio_service import MinioService
from app.models.receipts import Receipt, create_receipt


class ReceiptService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.receipt_repository = ReceiptRepository(db)
        self.minio_service = MinioService()

    async def upload_receipt(self, file: UploadFile, purchase_date: date, user_id: int) -> Receipt:
        """Upload new receipt"""
        # Upload image to MinIO
        image_path = await self.minio_service.upload_file(file)

        receipt = create_receipt(
            user_id=user_id, image_path=image_path, purchase_date=purchase_date
        )

        return await self.receipt_repository.save(receipt)

    async def upload_receipts(
        self, files: List[UploadFile], purchase_date: date, user_id: int
    ) -> int:
        """Upload new receipts"""
        receipts = []

        for file in files:
            image_path = await self.minio_service.upload_file(file)
            receipt = create_receipt(
                user_id=user_id, image_path=image_path, purchase_date=purchase_date
            )
            receipts.append(receipt)

        return await self.receipt_repository.save_many(receipts)

    async def get_receipts(
        self, user_id: int, last_id: int = sys.maxsize, limit: int = 5
    ) -> List[Receipt]:
        """Get user receipts"""
        return await self.receipt_repository.get_all(
            {"user_id": user_id, "last_id": last_id, "limit": limit}
        )

    async def get(self, id: int) -> Receipt | None:
        """Get receipt by Id"""
        return await self.receipt_repository.get_by_id(id)
