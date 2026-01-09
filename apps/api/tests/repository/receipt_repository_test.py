# tests/repository/test_receipt_repository.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.models.receipts import Receipt
from app.repository.receipt_repository import ReceiptRepository


@pytest.mark.asyncio
async def test_save_receipt(db: AsyncSession):
    """Test saving a receipt to database"""
    repo = ReceiptRepository(db)

    receipt = Receipt(
        user_id=1,
        image_path="minio://bucket/image.jpg",
        purchase_date=date(2025, 12, 1),
        status="uploaded",
    )

    saved = await repo.save(receipt)

    assert saved.id is not None
    assert saved.user_id == 1
    assert saved.image_path == "minio://bucket/image.jpg"


@pytest.mark.asyncio
async def test_get_receipt_by_id(db: AsyncSession):
    """Test retrieving receipt by ID"""
    repo = ReceiptRepository(db)

    # Create and save
    receipt = Receipt(user_id=1, image_path="test.jpg", purchase_date=date.today())
    saved = await repo.save(receipt)

    # Retrieve
    found = await repo.get_by_id(saved.id)

    assert found is not None
    assert found.id == saved.id


@pytest.mark.asyncio
async def test_get_all_by_user(db: AsyncSession):
    """Test retrieving all receipts for a user"""
    repo = ReceiptRepository(db)

    # Create multiple receipts
    for i in range(3):
        receipt = Receipt(user_id=1, image_path=f"image{i}.jpg", purchase_date=date.today())
        await repo.save(receipt)

    receipts = await repo.get_all({"user_id": 1, "last_id": -1, "limit": 3})

    assert len(receipts) >= 3


@pytest.mark.asyncio
async def test_get_receipt_by_id_not_found(db: AsyncSession):
    """Test retrieving non-existent receipt returns None"""
    repo = ReceiptRepository(db)

    # Try to get non-existent receipt
    found = await repo.get_by_id(999999)

    assert found is None


@pytest.mark.asyncio
async def test_save_many_receipts(db: AsyncSession):
    """Test saving multiple receipts at once"""
    repo = ReceiptRepository(db)

    # Create multiple receipts
    receipts = [
        Receipt(
            user_id=1,
            image_path=f"minio://bucket/image{i}.jpg",
            purchase_date=date(2025, 12, 1),
            status="uploaded",
        )
        for i in range(5)
    ]

    # Save all receipts
    count = await repo.save_many(receipts)

    assert count == 5

    # Verify they were saved
    all_receipts = await repo.get_all({"user_id": 1, "limit": 10})
    assert len(all_receipts) >= 5
