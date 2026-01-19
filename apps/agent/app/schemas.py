from typing import List, Optional
from pydantic import BaseModel, Field
from shared.types import ReceiptMetadata, LineItem, ValidationResult


class ExtractionRequest(BaseModel):
    """Request to extract data from receipt"""

    receipt_id: int = Field(..., description="Receipt ID from database")
    image_path: str = Field(..., description="MinIO path (minio://bucket/object)")
    user_id: int = Field(default=1, description="User ID for context")


class ExtractionResponse(BaseModel):
    """Agent extraction response (extends ExtractionResult)."""

    receipt_id: int
    metadata: ReceiptMetadata
    items: List[LineItem] = Field(default_factory=list)
    raw_text: Optional[str] = None
    validation: ValidationResult
    processing_time_ms: int
    success: bool = True
    error_message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "receipt_id": 123,
                "metadata": {
                    "merchant_name": "Whole Foods Market",
                    "purchase_date": "2026-01-15",
                    "total_amount": "47.23",
                    "currency": "USD",
                    "confidence": 0.92,
                },
                "items": [
                    {
                        "item_name": "Organic Bananas",
                        "quantity": 1,
                        "unit_price": "3.49",
                        "total_price": "3.49",
                        "confidence": 0.88,
                    }
                ],
                "validation": {"valid": True, "errors": [], "warnings": [], "confidence": 0.92},
                "processing_time_ms": 1243,
                "success": True,
            }
        }


class OCRStatusResponse(BaseModel):
    """OCR processing status check response."""

    receipt_id: int
    status: str
    progress_percent: int = Field(ge=0, le=100)
    message: str
