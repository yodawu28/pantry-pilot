from datetime import date
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.receipts import Receipt
from app.routers.response.receipt import ReceiptResponse, ReceiptsResponse
from app.services.minio_service import MinioService



router = APIRouter(prefix="/receipts", tags=["receipts"])
minio_service = MinioService()

@router.post("", status_code=201, response_model=ReceiptResponse)
async def upload_receipt(
    file: UploadFile = File(...),
    purchase_date: date = Form(...),
    user_id: int = Form(1),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload receipt image
    
    - **file**: Image file (jpg/png/jpeg)
    - **purchase_date**: Date of purchase
    - **user_id**: User ID (default: 1)
    """

    # Upload image to MinIO
    image_path = await minio_service.upload_file(file)

    # save to DB
    receipt = Receipt(
        user_id = user_id,
        image_path = image_path,
        purchase_date = purchase_date,
        status = "uploaded"
    )

    db.add(receipt)
    await db.commit()
    await db.refresh(receipt)

    return ReceiptResponse(
        id = receipt.id,
        user_id=receipt.user_id,
        image_path=receipt.image_path,
        purchase_date=str(receipt.purchase_date),
        status=receipt.status,
        created_at=receipt.created_at.isoformat()
    )

@router.get("", response_model=ReceiptsResponse)
async def list_receipts(
        user_id: int = 1,
        db: AsyncSession = Depends(get_db)
):
    """
    Get all receipts for a user

    - **user_id**: User ID (default = 1)
    """

    result = await db.execute(select(Receipt).where(Receipt.user_id == user_id))
    receipts = result.scalars().all()

    responses = [ReceiptResponse(
        id = receipt.id,
        user_id=receipt.user_id,
        image_path=receipt.image_path,
        purchase_date=str(receipt.purchase_date),
        status=receipt.status,
        created_at=receipt.created_at.isoformat()

    ) for receipt in receipts]

    return ReceiptsResponse(
        total = len(responses),
        receipts=responses
    )
