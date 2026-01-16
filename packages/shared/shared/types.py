
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class OCRStatus(str, Enum):
    """Receipt OCR processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReceiptMetadata(BaseModel):
    """Extract receipt metadata."""
    merchant_name: Optional[str] = Field(default=None, max_length=200)
    purchase_date: Optional[date] = None
    total_amount: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    currency: str = Field(default="VND", max_length=5)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class LineItem(BaseModel):
    """Single receipt line item."""
    item_name: str = Field(..., max_length=200)
    quantity: float = Field(default=1.0, ge=0.001)  # Changed to float for items sold by weight (e.g., 0.246 kg)
    unit_price: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    total_price: Decimal = Field(..., ge=0, decimal_places=2)
    currency: str = Field(default="VND", max_length=5)  # Currency for this item
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)


class ValidationResult(BaseModel):
    """Validation result from MCP tool."""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)

class ExtractionResult(BaseModel):
    """Complete extraction result from agent."""
    metadata: ReceiptMetadata
    items: List[LineItem] = Field(default_factory=list)
    raw_text: Optional[str] = None
    validation: dict = Field(default_factory=dict)
    processing_time_ms: int
    success: bool = True
    error_message: Optional[str] = None

    class Config:
        son_schema_extra = {
            "example": {
                "metadata": {
                    "merchant_name": "Whole Foods Market",
                    "purchase_date": "2026-01-10",
                    "total_amount": "47.23",
                    "currency": "USD",
                    "confidence": 0.92
                },
                "items": [
                    {
                        "item_name": "Organic Bananas",
                        "quantity": 1,
                        "unit_price": "3.49",
                        "total_price": "3.49",
                        "confidence": 0.88
                    }
                ],
                "validation": {
                    "valid": True,
                    "errors": [],
                    "warnings": []
                },
                "processing_time_ms": 1243,
                "success": True
            }
        }


class ImageData(BaseModel):
    """Image data returned by MCP get_image_tool."""
    image_base64: str  # Base64-encoded image bytes
    content_type: str
    size_bytes: int
    width: Optional[int] = None
    height: Optional[int] = None


class ReceiptContext(BaseModel):
    """Context about receipt from database (for agent reasoning)"""
    receipt_id: int
    user_id: int
    previous_receipts_count: int
    merchant_history: List[str] = Field(default_factory=list)
    avg_total: Optional[Decimal] = None
