from pydantic import BaseModel, ConfigDict
from typing import List


class ReceiptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    image_path: str
    purchase_date: str
    status: str
    ocr_status: str
    created_at: str


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