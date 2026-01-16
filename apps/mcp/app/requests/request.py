from pydantic import BaseModel

from shared.types import LineItem, ReceiptMetadata


class GetImageRequest(BaseModel):
    image_path: str


class ValidateRequest(BaseModel):
    metadata: ReceiptMetadata
    items: list[LineItem]


class GetContextRequest(BaseModel):
    receipt_id: int
    user_id: int
