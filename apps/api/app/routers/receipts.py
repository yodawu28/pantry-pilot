from datetime import date
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.response.receipt import ReceiptResponse, ReceiptsResponse
from app.services.minio_service import MinioService
from app.services.receipt_service import ReceiptService


router = APIRouter(prefix="/receipts", tags=["receipts"])
minio_service = MinioService()


@router.post("", status_code=201, response_model=ReceiptResponse)
async def upload_receipt(
    file: UploadFile = File(...),
    purchase_date: date = Form(...),
    user_id: int = Form(1),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload receipt image

    - **file**: Image file (jpg/png/jpeg)
    - **purchase_date**: Date of purchase
    - **user_id**: User ID (default: 1)
    """

    receipt_service = ReceiptService(db)
    receipt = await receipt_service.upload_receipt(file, purchase_date, user_id)

    return ReceiptResponse(
        id=receipt.id,
        user_id=receipt.user_id,
        image_path=receipt.image_path,
        purchase_date=str(receipt.purchase_date),
        status=receipt.status,
        created_at=receipt.created_at.isoformat(),
    )


@router.get("", response_model=ReceiptsResponse)
async def list_receipts(
    last_id: int = -1, limit: int = 50, user_id: int = 1, db: AsyncSession = Depends(get_db)
):
    """
    Get all receipts for a user

    - **user_id**: User ID (default = 1)
    """

    receipt_service = ReceiptService(db)
    receipts = await receipt_service.get_receipts(user_id, last_id, limit)

    responses = [
        ReceiptResponse(
            id=receipt.id,
            user_id=receipt.user_id,
            image_path=receipt.image_path,
            purchase_date=str(receipt.purchase_date),
            status=receipt.status,
            created_at=receipt.created_at.isoformat(),
        )
        for receipt in receipts
    ]

    last_id = -1
    if len(responses) > 0:
        last_id = responses[-1].id

    return ReceiptsResponse(total=len(responses), receipts=responses, last_id=last_id)
