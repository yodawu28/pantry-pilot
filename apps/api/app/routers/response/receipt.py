from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class LineItemResponse(BaseModel):
    """Line item in receipt"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    receipt_id: int
    item_name: str
    quantity: float
    unit_price: str
    total_price: str
    currency: str
    confidence: Optional[float] = None


class ReceiptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    image_path: str
    purchase_date: str
    status: str
    ocr_status: str
    created_at: str
    # Optional fields from OCR extraction
    merchant_name: Optional[str] = None
    total_amount: Optional[str] = None
    currency: Optional[str] = None
    ocr_text: Optional[str] = None
    # Related data
    items: Optional[List[LineItemResponse]] = None


class ReceiptsUploadResponse(BaseModel):
    total: int


class ReceiptsResponse(BaseModel):
    total: int
    receipts: List[ReceiptResponse]
    last_id: int


class OCRResponse(BaseModel):
    """Response for OCR trigger endpoint"""

    receipt_id: int
    status: str
    message: str
