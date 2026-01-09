# tests/services/test_receipt_service.py
import pytest
from unittest.mock import AsyncMock
from datetime import date
from fastapi import UploadFile
from app.services.receipt_service import ReceiptService
from app.models.receipts import Receipt


@pytest.mark.asyncio
async def test_upload_receipt(mocker):
    """Test upload receipt business logic"""
    # Mock dependencies
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    mock_minio = AsyncMock()

    # Mock the repository
    mocker.patch("app.services.receipt_service.ReceiptRepository", return_value=mock_repo)
    mocker.patch("app.services.receipt_service.MinioService", return_value=mock_minio)

    mock_minio.upload_file.return_value = "minio://bucket/image.jpg"

    receipt = Receipt(
        id=1,
        user_id=1,
        image_path="minio://bucket/image.jpg",
        purchase_date=date(2025, 12, 1),
        status="uploaded",
    )
    mock_repo.save.return_value = receipt

    # Create service
    service = ReceiptService(mock_db)
    service.receipt_repository = mock_repo
    service.minio_service = mock_minio

    # Test
    mock_file = AsyncMock(spec=UploadFile)
    result = await service.upload_receipt(mock_file, date(2025, 12, 1), user_id=1)

    assert result.id == 1
    assert result.status == "uploaded"
    mock_minio.upload_file.assert_called_once()
    mock_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_get_receipts(mocker):
    """Test getting receipts"""
    mock_db = AsyncMock()
    mock_repo = AsyncMock()

    receipts = [
        Receipt(id=1, user_id=1, image_path="img1.jpg", purchase_date=date.today()),
        Receipt(id=2, user_id=1, image_path="img2.jpg", purchase_date=date.today()),
    ]
    mock_repo.get_all.return_value = receipts

    mocker.patch("app.services.receipt_service.ReceiptRepository", return_value=mock_repo)

    service = ReceiptService(mock_db)
    service.receipt_repository = mock_repo

    result = await service.get_receipts(1)

    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_receipt_by_id(mocker):
    """Test get receipt by ID"""
    mock_db = AsyncMock()
    mock_repo = AsyncMock()

    receipt = Receipt(
        id=1, user_id=1, image_path="img1.jpg", purchase_date=date.today(), status="uploaded"
    )
    mock_repo.get_by_id.return_value = receipt

    mocker.patch("app.services.receipt_service.ReceiptRepository", return_value=mock_repo)

    service = ReceiptService(mock_db)
    service.receipt_repository = mock_repo

    result = await service.get(1)

    assert result is not None
    assert result.id == 1
    mock_repo.get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_receipt_by_id_not_found(mocker):
    """Test get receipt by ID when not found"""
    mock_db = AsyncMock()
    mock_repo = AsyncMock()

    mock_repo.get_by_id.return_value = None

    mocker.patch("app.services.receipt_service.ReceiptRepository", return_value=mock_repo)

    service = ReceiptService(mock_db)
    service.receipt_repository = mock_repo

    result = await service.get(999)

    assert result is None
    mock_repo.get_by_id.assert_called_once_with(999)


@pytest.mark.asyncio
async def test_upload_multiple_receipts(mocker):
    """Test uploading multiple receipts"""
    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    mock_minio = AsyncMock()

    mocker.patch("app.services.receipt_service.ReceiptRepository", return_value=mock_repo)
    mocker.patch("app.services.receipt_service.MinioService", return_value=mock_minio)

    # Mock MinIO to return different paths for each file
    mock_minio.upload_file.side_effect = [
        "minio://bucket/image1.jpg",
        "minio://bucket/image2.jpg",
        "minio://bucket/image3.jpg",
    ]

    # Mock save_many to return count
    mock_repo.save_many.return_value = 3

    service = ReceiptService(mock_db)
    service.receipt_repository = mock_repo
    service.minio_service = mock_minio

    # Create mock files
    mock_files = [AsyncMock(spec=UploadFile) for _ in range(3)]

    # Test
    count = await service.upload_receipts(mock_files, date(2025, 12, 1), user_id=1)

    assert count == 3
    assert mock_minio.upload_file.call_count == 3
    mock_repo.save_many.assert_called_once()

    # Verify receipts list passed to save_many
    receipts_arg = mock_repo.save_many.call_args[0][0]
    assert len(receipts_arg) == 3
