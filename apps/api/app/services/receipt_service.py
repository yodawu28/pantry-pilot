from datetime import date
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.receipt_repository import ReceiptRepository
from app.services.minio_service import MinioService
from app.models.receipts import Receipt, create_receipt


class ReceiptService:
    def __init__(self, db: AsyncSession, minio_service: Optional[MinioService] = None) -> None:
        self.db = db
        self.receipt_repository = ReceiptRepository(db)
        self.minio_service = minio_service or MinioService()

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
    ) -> List[Receipt]:
        """Upload new receipts and return the created receipts"""
        receipts = []

        for file in files:
            image_path = await self.minio_service.upload_file(file)
            receipt = create_receipt(
                user_id=user_id, image_path=image_path, purchase_date=purchase_date
            )
            receipts.append(receipt)

        await self.receipt_repository.save_many(receipts)
        return receipts

    async def get_receipts(
        self, user_id: int, last_id: int = -1, limit: int = 5, params = {}
    ) -> List[Receipt]:
        """Get user receipts"""
        params['user_id'] = user_id
        params["last_id"] = last_id
        params["limit"] = limit
        return await self.receipt_repository.get_all(params=params)

    async def get(self, id: int) -> Receipt | None:
        """Get receipt by Id"""
        return await self.receipt_repository.get_by_id(id)

    async def get_with_items(self, id: int) -> Receipt | None:
        """Get receipt by Id with line items"""
        return await self.receipt_repository.get_by_id_with_items(id)

    async def count(self, params = {}) -> int:
        """Count receipts"""
        return await self.receipt_repository.count(params=params)
        
