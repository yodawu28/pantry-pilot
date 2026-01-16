import time
import httpx
import base64
import json
from datetime import datetime
from typing import Optional
from openai import OpenAI
from app.config import settings
from app.schemas import ExtractionRequest, ExtractionResponse
from app.vision_service import VisionService
from app.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from shared.types import (
    ReceiptMetadata,
    LineItem,
    ValidationResult,
    ImageData,
    ReceiptContext,
)


class ReceiptAgent:
    """
    Agent for extracting receipt data using EasyOCR + Gemma-3 vision model + MCP tools.

    NEW Workflow:
    1. Call MCP OCR tool (EasyOCR) to extract raw text from image
    2. Fetch image from storage (via MCP)
    3. Pass both RAW TEXT + IMAGE to Gemma-3
    4. Gemma-3 acts as "editor" - uses raw text for accuracy, image for structure
    5. Validate extraction (via MCP)
    6. Return structured JSON (API handles DB save)
    """

    def __init__(self):
        self.mcp_url = settings.mcp_url
        self.vision_service = VisionService(max_size=settings.max_image_size)
        self.client = httpx.AsyncClient(timeout=settings.timeout_seconds)
        self.openai_client = OpenAI(api_key=settings.openai_api_key)

    async def extract_from_receipt(self, request: ExtractionRequest) -> ExtractionResponse:
        """
        Main extraction method called by API.

        Args:
            request: ExtractionRequest with receipt_id, image_path, user_id

        Returns:
            ExtractionResponse with extracted data (JSON only)
        """
        start_time = time.time()

        try:
            # Step 1: Call MCP OCR tool to extract raw text
            print(f"[Agent] Step 1: Calling EasyOCR via MCP for receipt {request.receipt_id}")
            ocr_result = await self._call_mcp_ocr(request.image_path)

            if not ocr_result.get("success"):
                raise Exception(f"OCR failed: {ocr_result.get('error', 'Unknown error')}")

            raw_text = ocr_result.get("raw_text", "")
            print(f"[Agent] ✓ OCR extracted {len(raw_text)} characters")
            print(f"[Agent] Raw OCR preview: {raw_text[:200]}...")

            # Step 2: Get image from storage via MCP
            print(f"[Agent] Step 2: Fetching image: {request.image_path}")
            image_data = await self._call_mcp_get_image(request.image_path)

            # Decode base64 image
            image_bytes = base64.b64decode(image_data.image_base64)

            # Step 3: Preprocess image
            if settings.image_preprocessing:
                print("[Agent] Step 3: Preprocessing image...")
                processed_bytes = await self.vision_service.preprocess(image_bytes)
            else:
                processed_bytes = image_bytes

            # Step 4: Get receipt context (optional, for agent reasoning)
            context = await self._call_mcp_get_context(request.receipt_id, request.user_id)
            context_str = self._format_context(context)

            # Step 5: Call Gemma-3 with RAW OCR TEXT + IMAGE
            print("[Agent] Step 5: Calling Gemma-3 with OCR text + image...")
            extraction_data = await self._call_gemma_vision(
                processed_bytes,
                raw_ocr_text=raw_text,  # NEW: Pass OCR text
                receipt_id=request.receipt_id,
                context=context_str,
            )

            # Step 5: Parse Gemma's JSON response
            metadata = ReceiptMetadata(**extraction_data["metadata"])
            items = [LineItem(**item) for item in extraction_data.get("items", [])]
            raw_text_final = (
                extraction_data.get("raw_text") or raw_text
            )  # Use OCR text if model doesn't provide

            # Step 6: Validate extraction via MCP
            print("[Agent] Validating extraction...")
            validation = await self._call_mcp_validate(metadata, items)

            processing_time_ms = int((time.time() - start_time) * 1000)

            return ExtractionResponse(
                receipt_id=request.receipt_id,
                metadata=metadata,
                items=items,
                raw_text=raw_text_final,
                validation=validation,
                processing_time_ms=processing_time_ms,
                success=validation.valid,
                error_message=None if validation.valid else ", ".join(validation.errors),
            )

        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            print(f"[Agent] Extraction failed: {e}")

            return ExtractionResponse(
                receipt_id=request.receipt_id,
                metadata=ReceiptMetadata(confidence=0.0),
                items=[],
                raw_text=None,
                validation=ValidationResult(
                    valid=False, errors=[str(e)], warnings=[], confidence=0.0
                ),
                processing_time_ms=processing_time_ms,
                success=False,
                error_message=f"Agent extraction failed: {str(e)}",
            )

    async def _call_gemma_vision(
        self,
        image_bytes: bytes,
        raw_ocr_text: str,  # NEW: OCR extracted text
        receipt_id: int,
        context: str,
    ) -> dict:
        """
        Call Gemma-3 model via Ollama to extract receipt data.

        NEW: Uses EasyOCR text + image for better accuracy
        - OCR text provides accurate numbers
        - Image provides structure/layout understanding

        Args:
            image_bytes: Preprocessed image bytes
            raw_ocr_text: Raw text extracted by EasyOCR
            receipt_id: Receipt ID for logging
            context: Formatted context string

        Returns:
            Extracted data as dict with metadata, items, and raw_text
        """
        response_text = ""  # Initialize to avoid unbound variable error
        try:
            # Convert image bytes to base64 for OpenAI
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            print(
                f"[Agent] Image encoded: {len(image_base64)} base64 chars ({len(image_bytes)} bytes)"
            )

            # Format the prompt with context AND OCR text
            user_prompt = USER_PROMPT_TEMPLATE.format(
                receipt_id=receipt_id,
                image_path="<provided>",
                user_id="<current>",
                context=context,
                raw_ocr_text=raw_ocr_text,
            )

            print(f"[Agent] Calling OpenAI with model: {settings.openai_model}")
            print(f"[Agent] Sending image to vision model for receipt {receipt_id}")

            # Call OpenAI
            response_text = await self._call_openai(user_prompt, image_base64)

            print(f"[Agent] Model response length: {len(response_text)} chars")
            print(f"[Agent] Raw response: {response_text[:500]}")

            # Parse JSON from response (handle markdown code blocks if present)
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith("```"):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove trailing ```
            response_text = response_text.strip()

            # Fix common typo from model: "purcahse_date" → "purchase_date"
            response_text = response_text.replace('"purcahse_date"', '"purchase_date"')

            # Fix incomplete JSON (model response may be truncated)
            if not response_text.endswith("}"):
                # Try to close incomplete JSON
                # Count braces to see how many closing braces we need
                open_braces = response_text.count("{")
                close_braces = response_text.count("}")

                # Close any open strings
                if response_text.count('"') % 2 == 1:
                    response_text += '"'

                # Close objects
                for _ in range(open_braces - close_braces):
                    response_text += "\n}"

                print(
                    f"[Agent] ⚠️ Fixed incomplete JSON - added {open_braces - close_braces} closing braces"
                )

            # Parse JSON
            extraction_data = json.loads(response_text)

            # Normalize date format from DD/MM/YYYY to YYYY-MM-DD
            metadata_info = extraction_data.get("metadata", {})
            if "purchase_date" in metadata_info:
                metadata_info["purchase_date"] = self._normalize_date(
                    metadata_info["purchase_date"]
                )

            # Log extraction results for debugging
            print("[Agent] ✓ Extraction complete:")
            print(f"  - Merchant: {metadata_info.get('merchant_name', 'N/A')}")
            print(f"  - Date: {metadata_info.get('purchase_date', 'N/A')}")
            print(
                f"  - Total: {metadata_info.get('total_amount', 'N/A')} {metadata_info.get('currency', 'N/A')}"
            )
            print(f"  - Items: {len(extraction_data.get('items', []))} extracted")
            print(f"  - Confidence: {metadata_info.get('confidence', 0)}")
            if extraction_data.get("raw_text"):
                print(f"  - Raw text preview: {extraction_data['raw_text'][:200]}...")

            return extraction_data

        except json.JSONDecodeError as e:
            response_preview = response_text[:1000] if response_text else "N/A"
            print(f"[Agent] ✗ Failed to parse Gemma response as JSON: {e}")
            print(f"[Agent] Full response text: {response_preview}")
            print("[Agent] ⚠️ Returning mock data - check if model is vision-capable!")
            # Return mock data as fallback
            return self._get_mock_extraction()
        except Exception as e:
            print(f"[Agent] Gemma vision call failed: {e}")
            return self._get_mock_extraction()

    def _normalize_date(self, date_str: str) -> str:
        """
        Normalize date from various formats to YYYY-MM-DD.
        Handles: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, etc.
        """
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d")

        # Try common formats
        formats = [
            "%d/%m/%Y",  # Vietnamese: 29/10/2016
            "%d-%m-%Y",  # Alternative: 29-10-2016
            "%Y-%m-%d",  # ISO: 2016-10-29 (already correct)
            "%m/%d/%Y",  # US: 10/29/2016
            "%d.%m.%Y",  # European: 29.10.2016
        ]

        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str.strip(), fmt)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # If all parsing fails, return original and let Pydantic handle it
        print(f"[Agent] ⚠️ Could not parse date '{date_str}', using current date")
        return datetime.now().strftime("%Y-%m-%d")

    def _get_mock_extraction(self) -> dict:
        """Fallback mock extraction data for development/testing."""
        return {
            "metadata": {
                "merchant_name": "Mock Store",
                "purchase_date": "2026-01-15",
                "total_amount": "0.00",
                "currency": "USD",
                "confidence": 0.1,
            },
            "items": [],
            "raw_text": "Mock extraction - Gemma model unavailable",
        }

    async def _call_mcp_ocr(self, image_path: str) -> dict:
        """Call MCP OCR tool to extract raw text using EasyOCR."""
        response = await self.client.post(
            f"{self.mcp_url}/tools/ocr-text", json={"image_path": image_path}
        )
        response.raise_for_status()
        return response.json()

    async def _call_mcp_get_image(self, image_path: str) -> ImageData:
        """Call MCP tool to fetch image from storage."""
        response = await self.client.post(
            f"{self.mcp_url}/tools/get-image", json={"image_path": image_path}
        )
        response.raise_for_status()
        data = response.json()

        return ImageData(**data)

    async def _call_mcp_validate(
        self, metadata: ReceiptMetadata, items: list[LineItem]
    ) -> ValidationResult:
        """Call MCP validation tool."""
        try:
            response = await self.client.post(
                f"{self.mcp_url}/tools/validate",
                json={
                    "metadata": metadata.model_dump(mode="json"),
                    "items": [item.model_dump(mode="json") for item in items],
                },
            )
            response.raise_for_status()
            return ValidationResult(**response.json())
        except Exception as e:
            print(f"[Agent] ⚠️ Validation failed: {e}")
            # Return a basic validation result instead of failing
            return ValidationResult(
                valid=False,
                errors=[f"Validation service error: {str(e)}"],
                warnings=[],
                confidence=0.0,
            )

    async def _call_mcp_get_context(
        self, receipt_id: int, user_id: int
    ) -> Optional[ReceiptContext]:
        """Call MCP tool to get receipt context."""
        try:
            response = await self.client.post(
                f"{self.mcp_url}/tools/get-context",
                json={"receipt_id": receipt_id, "user_id": user_id},
            )
            response.raise_for_status()
            return ReceiptContext(**response.json())
        except Exception as e:
            print(f"[Agent] Failed to get context: {e}")
            return None

    def _format_context(self, context: Optional[ReceiptContext]) -> str:
        """Format context for prompt."""
        if not context:
            return "No previous purchase history available."

        avg_spending = f"${context.avg_total:.2f}" if context.avg_total else "N/A"
        merchants = ", ".join(context.merchant_history[:3]) if context.merchant_history else "None"

        return f"""User has {context.previous_receipts_count} previous receipts.
Recent merchants: {merchants}
Average spending: {avg_spending}"""

    async def _call_openai(self, user_prompt: str, image_base64: str) -> str:
        """Call OpenAI API with vision capability."""
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                            },
                        ],
                    },
                ],
                temperature=settings.openai_temperature,
                max_tokens=settings.openai_max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"[Agent] OpenAI API call failed: {e}")
            raise
