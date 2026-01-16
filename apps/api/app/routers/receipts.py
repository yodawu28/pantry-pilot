from datetime import date
from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.response.receipt import OCRResponse, ReceiptResponse, ReceiptsResponse, ReceiptsUploadResponse
from app.services.minio_service import MinioService
from app.services.ocr_service import OCRService
from app.services.receipt_service import ReceiptService


router = APIRouter(prefix="/receipts", tags=["receipts"])


def get_minio_service() -> MinioService:
    """Dependency to get MinioService instance"""
    return MinioService()


@router.post("", status_code=201, response_model=ReceiptResponse)
async def upload_receipt(
    file: UploadFile = File(...),
    purchase_date: date = Form(...),
    user_id: int = Form(1),
    db: AsyncSession = Depends(get_db),
    minio_service: MinioService = Depends(get_minio_service),
):
    """
    Upload receipt image

    - **file**: Image file (jpg/png/jpeg)
    - **purchase_date**: Date of purchase
    - **user_id**: User ID (default: 1)
    """

    receipt_service = ReceiptService(db, minio_service)
    receipt = await receipt_service.upload_receipt(file, purchase_date, user_id)

    return ReceiptResponse(
        id=receipt.id,
        user_id=receipt.user_id,
        image_path=receipt.image_path,
        purchase_date=str(receipt.purchase_date),
        status=receipt.status,
        ocr_status=receipt.ocr_status,
        created_at=receipt.created_at.isoformat() if receipt.created_at else "",
    )


@router.post("/bulk", status_code=201, response_model=ReceiptsUploadResponse)
async def upload_receipts(
    files: List[UploadFile] = File(...),
    purchase_date: date = Form(...),
    user_id: int = Form(1),
    db: AsyncSession = Depends(get_db),
    minio_service: MinioService = Depends(get_minio_service),
):
    """
    Upload multiple receipt images

    - **files**: List of image files (jpg/png/jpeg)
    - **purchase_date**: Date of purchase
    - **user_id**: User ID (default: 1)
    """

    receipt_service = ReceiptService(db, minio_service)
    total = await receipt_service.upload_receipts(files, purchase_date, user_id)

    return ReceiptsUploadResponse(total=total)


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
            ocr_status=receipt.ocr_status,
            created_at=receipt.created_at.isoformat() if receipt.created_at else "",
        )
        for receipt in receipts
    ]

    last_id = -1
    if len(responses) > 0:
        last_id = responses[-1].id

    return ReceiptsResponse(total=len(responses), receipts=responses, last_id=last_id)


@router.get("/{id}", response_model=ReceiptResponse)
async def get_receipt(id: int, db: AsyncSession = Depends(get_db)):
    """
    Get receipt by id

    - **id**: Id of receipt
    """

    receipt_service = ReceiptService(db)
    receipt = await receipt_service.get(id)

    if not receipt:
        raise HTTPException(status_code=404, detail=f"Receipt with id {id} not found")

    return ReceiptResponse(
        id=receipt.id,
        user_id=receipt.user_id,
        image_path=receipt.image_path,
        purchase_date=str(receipt.purchase_date),
        status=receipt.status,
        ocr_status=receipt.ocr_status,
        created_at=receipt.created_at.isoformat() if receipt.created_at else "",
    )


@router.post("/{id}/ocr", response_model=OCRResponse)
async def trigger_ocr(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger OCR extraction for a receipt.

    - **id**: Receipt ID to process
    """
    receipt_service = ReceiptService(db)
    receipt = await receipt_service.get(id)

    if not receipt:
        raise HTTPException(status_code=404, detail=f"Receipt with id {id} not found")

    ocr_service = OCRService()

    try:
        await ocr_service.extract_receipt(
            receipt_id=receipt.id,
            image_path=receipt.image_path,
            user_id=receipt.user_id,
            db=db,
        )
        return OCRResponse(
            receipt_id=id,
            status="processing",
            message="OCR extraction started successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR extraction failed: {str(e)}")


@router.post("/{id}/ocr/retry", response_model=OCRResponse)
async def retry_ocr(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Retry OCR extraction for a failed receipt.

    - **id**: Receipt ID to retry
    """
    receipt_service = ReceiptService(db)
    receipt = await receipt_service.get(id)

    if not receipt:
        raise HTTPException(status_code=404, detail=f"Receipt with id {id} not found")

    ocr_service = OCRService()

    try:
        await ocr_service.retry_extraction(
            receipt_id=receipt.id,
            image_path=receipt.image_path,
            user_id=receipt.user_id,
            db=db,
        )
        return OCRResponse(
            receipt_id=id,
            status="processing",
            message="OCR extraction retry started successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR retry failed: {str(e)}")


@router.get("/{id}/ocr/status")
async def get_ocr_status(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get OCR extraction status for a receipt.

    - **id**: Receipt ID
    """
    receipt_service = ReceiptService(db)
    receipt = await receipt_service.get(id)

    if not receipt:
        raise HTTPException(status_code=404, detail=f"Receipt with id {id} not found")

    ocr_service = OCRService()
    status = await ocr_service.get_extraction_status(id)

    return status
