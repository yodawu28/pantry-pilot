from datetime import date
from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.response.receipt import (
    OCRResponse,
    ReceiptResponse,
    ReceiptsResponse,
    ReceiptsUploadResponse,
    LineItemResponse,
)
from app.services.minio_service import MinioService
from app.services.ocr_service import OCRService
from app.services.receipt_service import ReceiptService
from app.services.queue_client import simple_queue_client


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
    Upload receipt image and automatically queue for OCR processing

    - **file**: Image file (jpg/png/jpeg)
    - **purchase_date**: Date of purchase
    - **user_id**: User ID (default: 1)
    """

    receipt_service = ReceiptService(db, minio_service)
    receipt = await receipt_service.upload_receipt(file, purchase_date, user_id)

    # Automatically queue for OCR processing
    try:
        job_id = simple_queue_client.enqueue_ocr_task(
            receipt_id=receipt.id, image_path=receipt.image_path, user_id=receipt.user_id
        )
        print(f"[API] Queued OCR for receipt {receipt.id}: {job_id}")
    except Exception as e:
        print(f"[API] Failed to queue OCR for receipt {receipt.id}: {str(e)}")
        # Don't fail the upload if queue fails

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
    Upload multiple receipt images and automatically queue for OCR processing

    - **files**: List of image files (jpg/png/jpeg)
    - **purchase_date**: Date of purchase
    - **user_id**: User ID (default: 1)
    """

    receipt_service = ReceiptService(db, minio_service)
    receipts = await receipt_service.upload_receipts(files, purchase_date, user_id)

    # Automatically queue all receipts for OCR processing
    job_ids = []
    queued = 0
    for receipt in receipts:
        try:
            job_id = simple_queue_client.enqueue_ocr_task(
                receipt_id=receipt.id, image_path=receipt.image_path, user_id=receipt.user_id
            )
            job_ids.append(job_id)
            queued += 1
            print(f"[API] Queued OCR for receipt {receipt.id}: {job_id}")
        except Exception as e:
            print(f"[API] Failed to queue OCR for receipt {receipt.id}: {str(e)}")
            # Continue with other receipts

    return ReceiptsUploadResponse(total=len(receipts), queued=queued, job_ids=job_ids)


@router.get("", response_model=ReceiptsResponse)
async def list_receipts(
    last_id: int = -1, limit: int = 50, user_id: int = 1, db: AsyncSession = Depends(get_db)
):
    """
    Get all receipts for a user

    - **user_id**: User ID (default = 1)
    - **last_id**: Pagination cursor, receipts with id < last_id (default: -1 = no filter)
    - **limit**: Max number of receipts to return (default: 50)
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
            merchant_name=receipt.merchant_name,
            total_amount=str(receipt.total_amount) if receipt.total_amount else None,
            currency=receipt.currency,
            ocr_text=receipt.ocr_text,
        )
        for receipt in receipts
    ]

    last_id = -1
    if len(responses) > 0:
        last_id = responses[0].id

    return ReceiptsResponse(total=len(responses), receipts=responses, last_id=last_id)


@router.get("/{id}", response_model=ReceiptResponse)
async def get_receipt(id: int, db: AsyncSession = Depends(get_db)):
    """
    Get receipt by id with line items

    - **id**: Id of receipt
    """

    receipt_service = ReceiptService(db)
    receipt = await receipt_service.get_with_items(id)

    if not receipt:
        raise HTTPException(status_code=404, detail=f"Receipt with id {id} not found")

    # Build items list if available
    items_list = None
    if receipt.ocr_status == "completed" and hasattr(receipt, "items") and receipt.items:
        items_list = [
            LineItemResponse(
                id=item.id,
                receipt_id=item.receipt_id,
                item_name=item.item_name,
                quantity=float(str(item.quantity)) if item.quantity is not None else 0.0,
                unit_price=str(item.unit_price) if item.unit_price is not None else "0",
                total_price=str(item.total_price) if item.total_price is not None else "0",
                currency=str(item.currency) if item.currency is not None else "VND",
                confidence=float(str(item.confidence)) if item.confidence is not None else None,
            )
            for item in receipt.items
        ]

    return ReceiptResponse(
        id=receipt.id,
        user_id=receipt.user_id,
        image_path=receipt.image_path,
        purchase_date=str(receipt.purchase_date),
        status=receipt.status,
        ocr_status=receipt.ocr_status,
        created_at=receipt.created_at.isoformat() if receipt.created_at else "",
        merchant_name=receipt.merchant_name,
        total_amount=str(receipt.total_amount) if receipt.total_amount else None,
        currency=receipt.currency,
        ocr_text=receipt.ocr_text,
        items=items_list,
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


@router.post("/ocr/process-all")
async def process_all_receipts(
    user_id: int = 1,
    limit: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger OCR processing for all pending receipts using Redis Queue.

    - **user_id**: User ID (default: 1)
    - **limit**: Optional limit on number of receipts to process

    Uses RQ (Redis Queue) for distributed task processing.
    """
    if not simple_queue_client.available:
        raise HTTPException(
            status_code=503, detail="Queue service not available. Please check Redis connection."
        )

    try:
        # Get all pending receipts
        receipt_service = ReceiptService(db)
        jobs = []

        last_id = -1
        page_limit = 5

        while True:
            # Get pending receipts page by page
            receipts = await receipt_service.get_receipts(
                user_id, last_id, page_limit, params={"ocr_status": "pending"}
            )

            if len(receipts) == 0:
                break

            # Enqueue each receipt
            for receipt in receipts:
                job = simple_queue_client.enqueue_ocr_task(
                    receipt_id=receipt.id,
                    image_path=receipt.image_path,
                    user_id=user_id,
                )
                if job:
                    jobs.append(job)

            last_id = receipts[-1].id
            break

        return {
            "status": "queued",
            "message": f"Queued {len(jobs)} receipts for OCR processing",
            "user_id": user_id,
            "queued": len(jobs),
            "job_ids": [job.id for job in jobs],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue receipts: {str(e)}")


@router.get("/ocr/queue-status")
async def get_queue_status(receipt_id: int | None = None):
    """
    Get OCR queue status from Redis Queue.

    - **receipt_id**: Optional receipt ID to check specific receipt status

    Returns current queue state.
    """
    if not simple_queue_client.available:
        raise HTTPException(status_code=503, detail="Queue service not available")

    try:
        if receipt_id:
            # Get specific job status
            job_status = simple_queue_client.get_job_status(f"ocr-{receipt_id}")
            return {
                "receipt_id": receipt_id,
                **job_status,
            }

        # Return overall queue info
        queue_info = simple_queue_client.get_queue_info()
        return {
            "queue": queue_info,
            "service": "redis-queue",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue status: {str(e)}")
