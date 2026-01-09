import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock
from app.main import app
from app.routers.receipts import get_minio_service


@pytest.mark.asyncio
async def test_health_check():
    """Test health endpoint"""
    # Mock MinioService to prevent connection attempts during import
    mock_minio = MagicMock()
    app.dependency_overrides[get_minio_service] = lambda: mock_minio
    
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["service"] == "pantry-pilot-api"
    finally:
        app.dependency_overrides.clear()
