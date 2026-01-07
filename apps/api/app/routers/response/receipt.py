from pydantic import BaseModel
from typing import List


class ReceiptResponse(BaseModel):
    id: int
    user_id: int
    image_path: str
    purchase_date: str
    status: str
    created_at: str


class ReceiptsResponse(BaseModel):
    total: int
    receipts: List[ReceiptResponse]
