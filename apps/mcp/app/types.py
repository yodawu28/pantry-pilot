"""MCP Server request/response types."""

from typing import List
from pydantic import BaseModel, Field
from shared.types import ReceiptMetadata, LineItem


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    version: str


class GetImageRequest(BaseModel):
    """Request to get image from storage."""

    image_path: str = Field(..., description="MinIO path (minio://bucket/object)")


class GetContextRequest(BaseModel):
    """Request to get receipt context."""

    receipt_id: int
    user_id: int


class ValidateRequest(BaseModel):
    """Request to validate extraction results."""

    metadata: ReceiptMetadata
    items: List[LineItem] = Field(default_factory=list)
