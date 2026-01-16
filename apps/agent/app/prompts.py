SYSTEM_PROMPT = """Extract receipt data from the image and OCR text into JSON format.

Use the OCR text for accurate names and numbers. Use the image to understand layout.

Output ONLY valid JSON with this structure (no markdown, no explanations):

{
  "metadata": {
    "merchant_name": "store name from receipt",
    "purchase_date": "YYYY-MM-DD",
    "total_amount": "number only",
    "currency": "VND",
    "confidence": 0.9
  },
  "items": [
    {
      "item_name": "product name",
      "quantity": 1.0,
      "unit_price": "price",
      "total_price": "price",
      "currency": "VND",
      "confidence": 0.9
    }
  ],
  "raw_text": "ocr text here"
}

Rules:
- quantity: number (like 0.246 for kg items)
- prices: strings with numbers only (remove dots)
- Vietnamese receipts: "37.340" means remove dot → "37340"
- Find total from "Tổng tiền" or "Tổng cộng" line
"""

USER_PROMPT_TEMPLATE = """Extract this receipt into JSON.

OCR Text:
{raw_ocr_text}

Context: {context}

Find:
1. Merchant name (like "BÁCH HÓA XANH")
2. Date (DD/MM/YYYY → convert to YYYY-MM-DD)
3. Items with quantity, price
4. Total amount from "Tổng tiền" line

Return JSON only."""
