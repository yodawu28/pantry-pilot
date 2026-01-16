"""OCR service for calling Agent and saving results to database."""

import httpx
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models import Receipt, ReceiptItem
from shared.types import OCRStatus


class OCRService:
    """
    Service for orchestrating receipt OCR extraction.

    Workflow:
    1. Call Agent API for extraction
    2. Parse Agent's JSON response
    3. Save results to database
    4. Update receipt status
    """

    def __init__(self):
        self.agent_url = settings.agent_url
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minutes for slow OCR + model processing

    async def extract_receipt(
        self, receipt_id: int, image_path: str, user_id: int, db: AsyncSession
    ) -> Receipt:
        """
        Extract receipt data via Agent and save to database.

        Args:
            receipt_id: Receipt ID
            image_path: MinIO path (minio://bucket/object)
            user_id: User ID
            db: Database session

        Returns:
            Updated Receipt object
        """
        # Get receipt from DB
        result = await db.execute(select(Receipt).where(Receipt.id == receipt_id))
        receipt = result.scalar_one_or_none()
        if not receipt:
            raise ValueError(f"Receipt {receipt_id} not found")

        try:
            # Update status to processing
            receipt.ocr_status = OCRStatus.PROCESSING
            await db.commit()

            # Call Agent API
            print(f"[OCR] Calling agent for receipt {receipt_id}")
            response = await self.client.post(
                f"{self.agent_url}/extract",
                json={"receipt_id": receipt_id, "image_path": image_path, "user_id": user_id},
            )
            response.raise_for_status()
            extraction_result = response.json()

            # Save extraction results
            await self._save_extraction(receipt, extraction_result, db)

            # Update status
            receipt.ocr_status = (
                OCRStatus.COMPLETED if extraction_result["success"] else OCRStatus.FAILED
            )
            receipt.parsed_at = datetime.utcnow()

            await db.commit()
            await db.refresh(receipt)

            return receipt

        except Exception as e:
            import traceback

            error_msg = str(e) or "Unknown error"
            print(f"[OCR] Extraction failed: {error_msg}")
            traceback.print_exc()
            receipt.ocr_status = OCRStatus.FAILED
            receipt.extraction_errors = json.dumps([error_msg])
            await db.commit()
            raise

    async def _save_extraction(self, receipt: Receipt, extraction_result: dict, db: AsyncSession):
        """Save agent extraction results to database."""
        metadata = extraction_result["metadata"]
        items = extraction_result.get("items", [])
        validation = extraction_result.get("validation", {})

        # Update receipt metadata
        receipt.merchant_name = metadata.get("merchant_name")
        receipt.total_amount = metadata.get("total_amount")
        receipt.currency = metadata.get("currency", "USD")
        receipt.extraction_confidence = metadata.get("confidence")
        receipt.ocr_text = extraction_result.get("raw_text")

        # Parse purchase_date
        if metadata.get("purchase_date"):
            try:
                from datetime import datetime

                receipt.purchase_date = datetime.fromisoformat(metadata["purchase_date"])
            except Exception:
                pass

        # Save validation errors/warnings
        errors = validation.get("errors", []) + validation.get("warnings", [])
        if errors:
            receipt.extraction_errors = json.dumps(errors)

        # Save line items
        for item_data in items:
            item = ReceiptItem(
                receipt_id=receipt.id,
                item_name=item_data["item_name"],
                quantity=item_data.get("quantity", 1),
                unit_price=item_data.get("unit_price"),
                total_price=item_data["total_price"],
                confidence=item_data.get("confidence"),
            )
            db.add(item)

    async def get_extraction_status(self, receipt_id: int) -> dict:
        """
        Get extraction status from Agent.

        Returns:
            Status dict with progress info
        """
        try:
            response = await self.client.get(f"{self.agent_url}/extract/{receipt_id}/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "receipt_id": receipt_id,
                "status": "unknown",
                "progress_percent": 0,
                "message": str(e),
            }

    async def retry_extraction(
        self, receipt_id: int, image_path: str, user_id: int, db: AsyncSession
    ) -> Receipt:
        """Retry failed extraction."""
        # Reset status
        result = await db.execute(select(Receipt).where(Receipt.id == receipt_id))
        receipt = result.scalar_one_or_none()
        if receipt:
            receipt.ocr_status = OCRStatus.PENDING
            receipt.extraction_errors = None
            await db.commit()

        return await self.extract_receipt(receipt_id, image_path, user_id, db)
