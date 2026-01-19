"""OCR processing tasks"""

import httpx
import asyncio
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from pantry_queue.config import settings


def parse_date(date_str: str | None) -> date | None:
    """Parse date string to date object."""
    if not date_str:
        return None
    try:
        # Try common formats
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None
    except Exception:
        return None


async def call_agent_extract(receipt_id: int, image_path: str, user_id: int) -> dict:
    """
    Call agent service to extract receipt data.

    Args:
        receipt_id: Receipt ID
        image_path: Image path in MinIO
        user_id: User ID

    Returns:
        Extraction result from agent
    """
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{settings.agent_url}/extract",
            json={
                "receipt_id": receipt_id,
                "image_path": image_path,
                "user_id": user_id,
            },
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Agent extraction failed: {response.status_code} - {response.text}")


async def save_extraction_result(receipt_id: int, result: dict):
    """
    Save extraction result to database.

    Updates receipt and inserts line items.

    Args:
        receipt_id: Receipt ID
        result: Extraction result from agent
    """
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Extract metadata from result (agent returns metadata at top level)
            metadata = result.get("metadata", {})

            # Update receipt with extracted data
            merchant_name = metadata.get("merchant_name")
            total_amount = metadata.get("total_amount")
            currency = metadata.get("currency", "VND")
            purchase_date = parse_date(metadata.get("purchase_date"))
            confidence = metadata.get("confidence", 0.0)

            # Build update query
            update_sql = """
                UPDATE receipts SET
                    ocr_status = 'completed',
                    merchant_name = COALESCE(:merchant_name, merchant_name),
                    total_amount = COALESCE(:total_amount, total_amount),
                    currency = COALESCE(:currency, currency),
                    purchase_date = COALESCE(:purchase_date, purchase_date),
                    extraction_confidence = :confidence,
                    parsed_at = NOW(),
                    updated_at = NOW()
                WHERE id = :receipt_id
            """

            await session.execute(
                text(update_sql),
                {
                    "receipt_id": receipt_id,
                    "merchant_name": merchant_name,
                    "total_amount": float(total_amount) if total_amount else None,
                    "currency": currency,
                    "purchase_date": purchase_date,
                    "confidence": confidence,
                },
            )

            # Delete existing line items for this receipt
            await session.execute(
                text("DELETE FROM receipt_items WHERE receipt_id = :receipt_id"),
                {"receipt_id": receipt_id},
            )

            # Insert line items (agent returns items at top level with item_name)
            items = result.get("items", [])
            for item in items:
                # Agent uses 'item_name', not 'name'
                item_name = item.get("item_name") or item.get("name", "Unknown Item")
                quantity = item.get("quantity", 1)
                unit_price = item.get("unit_price", 0)
                total_price = item.get("total_price", 0)
                item_currency = item.get("currency", "VND")
                confidence = item.get("confidence", 0.0)

                insert_sql = """
                    INSERT INTO receipt_items 
                        (receipt_id, item_name, quantity, unit_price, total_price, currency, confidence, created_at, updated_at)
                    VALUES 
                        (:receipt_id, :item_name, :quantity, :unit_price, :total_price, :currency, :confidence, NOW(), NOW())
                """

                await session.execute(
                    text(insert_sql),
                    {
                        "receipt_id": receipt_id,
                        "item_name": item_name,
                        "quantity": float(quantity) if quantity else 1.0,
                        "unit_price": float(unit_price) if unit_price else 0.0,
                        "total_price": float(total_price) if total_price else 0.0,
                        "currency": item_currency,
                        "confidence": float(confidence) if confidence else None,
                    },
                )

            await session.commit()
            print(f"[Queue Worker] Saved {len(items)} items for receipt {receipt_id}")

        except Exception as e:
            await session.rollback()
            raise e

    await engine.dispose()


async def update_receipt_status(receipt_id: int, ocr_status: str, error_message: str = None):
    """
    Update receipt OCR status in database.

    Args:
        receipt_id: Receipt ID
        ocr_status: New OCR status
        error_message: Optional error message for failed status
    """
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        if error_message:
            await session.execute(
                text(
                    """
                    UPDATE receipts 
                    SET ocr_status = :status, 
                        extraction_errors = :error,
                        updated_at = NOW() 
                    WHERE id = :id
                """
                ),
                {"status": ocr_status, "error": error_message, "id": receipt_id},
            )
        else:
            await session.execute(
                text("UPDATE receipts SET ocr_status = :status, updated_at = NOW() WHERE id = :id"),
                {"status": ocr_status, "id": receipt_id},
            )
        await session.commit()

    await engine.dispose()


def process_receipt_ocr(receipt_id: int, image_path: str, user_id: int) -> dict:
    """
    RQ task: Process OCR extraction for a receipt.

    This is the main worker task that RQ will execute.

    Args:
        receipt_id: Receipt ID
        image_path: Path to image in MinIO
        user_id: User ID

    Returns:
        Dict with task result
    """
    print(f"[Queue Worker] Processing OCR for receipt {receipt_id}")
    start_time = datetime.now()

    try:
        # Update status to processing
        asyncio.run(update_receipt_status(receipt_id, "processing"))

        # Call agent service
        result = asyncio.run(call_agent_extract(receipt_id, image_path, user_id))

        # Check if extraction was successful
        if result.get("success"):
            # Save extraction result to database
            asyncio.run(save_extraction_result(receipt_id, result))
        else:
            # Mark as failed with error message
            error_msg = result.get("error_message", "Extraction failed")
            asyncio.run(update_receipt_status(receipt_id, "failed", error_msg))

        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        print(f"[Queue Worker] ✓ Receipt {receipt_id} processed in {duration_ms}ms")

        return {
            "receipt_id": receipt_id,
            "status": "completed" if result.get("success") else "failed",
            "processing_time_ms": duration_ms,
            "result": result,
        }

    except Exception as e:
        # Mark as failed
        asyncio.run(update_receipt_status(receipt_id, "failed", str(e)))

        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        print(f"[Queue Worker] ✗ Receipt {receipt_id} failed: {str(e)}")

        return {
            "receipt_id": receipt_id,
            "status": "failed",
            "processing_time_ms": duration_ms,
            "error": str(e),
        }
