from pydantic import BaseModel, ConfigDict
from typing import List


class ReceiptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    image_path: str
    purchase_date: str
    status: str
    created_at: str


class ReceiptsResponse(BaseModel):
    total: int
    receipts: List[ReceiptResponse]
    last_id: int
