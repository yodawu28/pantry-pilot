# tests/routers/test_receipts_router.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from datetime import date, datetime, timezone
from fastapi import UploadFile
from app.main import app
from app.models.receipts import Receipt


@pytest.mark.asyncio
async def test_upload_receipt_endpoint(mocker):
    """Test POST /receipts endpoint"""
    # Mock service
    mock_service = AsyncMock()
    mock_receipt = Receipt(
        id=1,
        user_id=1,
        image_path="minio://bucket/image.jpg",
        purchase_date=date(2025, 12, 1),
        status="uploaded",
        created_at=datetime.now(timezone.utc)
    )
    mock_service.upload_receipt.return_value = mock_receipt
    
    mocker.patch(
        'app.routers.receipts.ReceiptService',
        return_value=mock_service
    )
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post(
            "/receipts",
            data={
                "user_id": "1",
                "purchase_date": "2025-12-01"
            },
            files={"file": ("test.jpg", b"fake_image_data", "image/jpeg")}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["status"] == "uploaded"


@pytest.mark.asyncio
async def test_list_receipts_endpoint(mocker):
    """Test GET /receipts endpoint"""
    mock_service = AsyncMock()
    mock_service.get_receipts.return_value = [
        Receipt(id=1, user_id=1, image_path="img1.jpg", purchase_date=date.today(), status="uploaded", created_at=datetime.now(timezone.utc)),
        Receipt(id=2, user_id=1, image_path="img2.jpg", purchase_date=date.today(), status="uploaded", created_at=datetime.now(timezone.utc)),
    ]
    
    mocker.patch(
        'app.routers.receipts.ReceiptService',
        return_value=mock_service
    )
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/receipts?user_id=1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert len(data["receipts"]) >= 2