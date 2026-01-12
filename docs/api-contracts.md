# API Contracts — PantryPilot

This document defines the request/response contracts for PantryPilot API.

**Versions:**
- W01: Healthcheck + Receipts upload + listing
- W02: OCR + Parsing + Review/Edit

Base URL
- Local: http://localhost:8000

Notes
- Auth is out of scope for W01-W02. Use a placeholder user_id (seeded user).
- All timestamps use ISO 8601.

---

## 1. Health

### GET /health
Description: Service healthcheck.

Status codes
| Code | Meaning |
|------|---------|
| 200  | OK      |

Response 200 (JSON)
```json
{ "status": "ok" }
```

---

## 2. Receipts

### 2.1 POST /receipts
Description: Upload a receipt image and create a receipt record.

Request
- Content-Type: multipart/form-data

Form fields
| Field          | Type           | Required | Allowed/Format                                 | Default            | Notes                      |
|----------------|----------------|----------|------------------------------------------------|--------------------|----------------------------|
| file           | image (binary) | Yes      | jpg, jpeg, png                                 | -                  | -                          |
| user_id        | UUID string    | Yes      | UUID v4                                        | -                  | Seeded user for W01        |
| purchase_date  | date string    | No       | YYYY-MM-DD                                     | Server local date  | -                          |
| source_type    | enum string    | No       | paper_receipt, app_screenshot, e_receipt_text | paper_receipt      | -                          |

Example (curl)
```bash
curl -X POST "http://localhost:8000/receipts" \
  -F "file=@./sample_receipt.jpg" \
  -F "user_id=00000000-0000-0000-0000-000000000001" \
  -F "purchase_date=2026-01-05" \
  -F "source_type=paper_receipt"
```

Response 201 (JSON)
```json
{
  "receipt": {
    "id": "b1f3f2a8-0b8e-4d7f-9c2d-9c1d0e7b8b2a",
    "user_id": "00000000-0000-0000-0000-000000000001",
    "source_type": "paper_receipt",
    "image_url": "s3://receipts/00000000-0000-0000-0000-000000000001/b1f3f2a8-0b8e-4d7f-9c2d-9c1d0e7b8b2a.jpg",
    "purchase_date": "2026-01-05",
    "status": "uploaded",
    "created_at": "2026-01-05T10:12:30Z",
    "updated_at": "2026-01-05T10:12:30Z"
  }
}
```

Errors
- 400 Bad Request: invalid source_type or missing required fields
- 413 Payload Too Large: file exceeds max size
- 415 Unsupported Media Type: not an allowed image type

Status codes
| Code | Meaning                                |
|------|----------------------------------------|
| 201  | Created                                |
| 400  | Bad Request                            |
| 413  | Payload Too Large                      |
| 415  | Unsupported Media Type                 |

Response 415 example (JSON)
```json
{
  "error": {
    "code": "UNSUPPORTED_MEDIA_TYPE",
    "message": "Only jpg, jpeg, png are supported."
  }
}
```

---

### 2.2 GET /receipts
Description: List receipts for a user (latest first).

Query params
| Param   | Type        | Required | Default        | Notes               |
|---------|-------------|----------|----------------|---------------------|
| user_id | UUID string | Yes      | -              | -                   |
| limit   | integer     | No       | 20 (max 100)   | Page size           |
| offset  | integer     | No       | 0              | Pagination offset   |

Example (curl)
```bash
curl "http://localhost:8000/receipts?user_id=00000000-0000-0000-0000-000000000001&limit=20&offset=0"
```

Response 200 (JSON)
```json
{
  "items": [
    {
      "id": "b1f3f2a8-0b8e-4d7f-9c2d-9c1d0e7b8b2a",
      "user_id": "00000000-0000-0000-0000-000000000001",
      "source_type": "paper_receipt",
      "purchase_date": "2026-01-05",
      "status": "uploaded",
      "created_at": "2026-01-05T10:12:30Z"
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total": 1
  }
}
```

Errors
- 400 Bad Request: missing or invalid user_id

Status codes
| Code | Meaning     |
|------|-------------|
| 200  | OK          |
| 400  | Bad Request |

---

### 2.3 GET /receipts/{receipt_id}
Description: Get receipt details.

Path params
| Param       | Type        | Required |
|-------------|-------------|----------|
| receipt_id  | UUID string | Yes      |

Example (curl)
```bash
curl "http://localhost:8000/receipts/b1f3f2a8-0b8e-4d7f-9c2d-9c1d0e7b8b2a"
```

Response 200 (JSON)
```json
{
  "receipt": {
    "id": "b1f3f2a8-0b8e-4d7f-9c2d-9c1d0e7b8b2a",
    "user_id": "00000000-0000-0000-0000-000000000001",
    "source_type": "paper_receipt",
    "image_url": "s3://receipts/00000000-0000-0000-0000-000000000001/b1f3f2a8-0b8e-4d7f-9c2d-9c1d0e7b8b2a.jpg",
    "purchase_date": "2026-01-05",
    "status": "uploaded",
    "created_at": "2026-01-05T10:12:30Z",
    "updated_at": "2026-01-05T10:12:30Z"
  }
}
```

Errors
- 404 Not Found: receipt_id does not exist

Response 404 example (JSON)
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Receipt not found."
  }
}
```

---

### 2.4 POST /receipts/{receipt_id}/ocr
**[W02]** Description: Trigger OCR processing (or reprocessing) for a receipt.

Path params
| Param       | Type        | Required |
|-------------|-------------|----------|
| receipt_id  | UUID string | Yes      |

Example (curl)
```bash
curl -X POST "http://localhost:8000/receipts/b1f3f2a8-0b8e-4d7f-9c2d-9c1d0e7b8b2a/ocr"
```

Response 202 (JSON) - Accepted
```json
{
  "message": "OCR processing started",
  "receipt_id": "b1f3f2a8-0b8e-4d7f-9c2d-9c1d0e7b8b2a",
  "ocr_status": "processing"
}
```

Errors
- 404 Not Found: receipt_id does not exist
- 409 Conflict: OCR already in progress

Status codes
| Code | Meaning                           |
|------|-----------------------------------|
| 202  | Accepted (processing started)     |
| 404  | Not Found                         |
| 409  | Conflict (already processing)     |

---

### 2.5 PATCH /receipts/{receipt_id}
**[W02]** Description: Update parsed receipt fields (manual corrections).

Path params
| Param       | Type        | Required |
|-------------|-------------|----------|
| receipt_id  | UUID string | Yes      |

Request (JSON)
```json
{
  "merchant_name": "Whole Foods Market",
  "total_amount": 45.67,
  "currency": "USD",
  "purchase_date": "2026-01-10"
}
```

Request body fields
| Field          | Type    | Required | Notes                           |
|----------------|---------|----------|---------------------------------|
| merchant_name  | string  | No       | Max 255 chars                   |
| total_amount   | decimal | No       | Positive number, 2 decimals     |
| currency       | string  | No       | ISO 4217 code (USD, EUR, etc.)  |
| purchase_date  | date    | No       | YYYY-MM-DD format               |

Example (curl)
```bash
curl -X PATCH "http://localhost:8000/receipts/b1f3f2a8-0b8e-4d7f-9c2d-9c1d0e7b8b2a" \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_name": "Whole Foods Market",
    "total_amount": 45.67,
    "currency": "USD"
  }'
```

Response 200 (JSON)
```json
{
  "receipt": {
    "id": "b1f3f2a8-0b8e-4d7f-9c2d-9c1d0e7b8b2a",
    "user_id": "00000000-0000-0000-0000-000000000001",
    "source_type": "paper_receipt",
    "image_url": "s3://receipts/00000000-0000-0000-0000-000000000001/b1f3f2a8-0b8e-4d7f-9c2d-9c1d0e7b8b2a.jpg",
    "purchase_date": "2026-01-10",
    "merchant_name": "Whole Foods Market",
    "total_amount": 45.67,
    "currency": "USD",
    "ocr_status": "completed",
    "status": "uploaded",
    "created_at": "2026-01-05T10:12:30Z",
    "updated_at": "2026-01-10T14:23:15Z"
  }
}
```

Errors
- 400 Bad Request: invalid field values (negative amount, invalid currency, future date)
- 404 Not Found: receipt_id does not exist

Status codes
| Code | Meaning     |
|------|-------------|
| 200  | OK          |
| 400  | Bad Request |
| 404  | Not Found   |

---

### 2.6 GET /receipts/{receipt_id}/ocr-status
**[W02]** Description: Check OCR processing status for a receipt.

Path params
| Param       | Type        | Required |
|-------------|-------------|----------|
| receipt_id  | UUID string | Yes      |

Example (curl)
```bash
curl "http://localhost:8000/receipts/b1f3f2a8-0b8e-4d7f-9c2d-9c1d0e7b8b2a/ocr-status"
```

Response 200 (JSON)
```json
{
  "receipt_id": "b1f3f2a8-0b8e-4d7f-9c2d-9c1d0e7b8b2a",
  "ocr_status": "completed",
  "ocr_text": "WHOLE FOODS MARKET\n123 Main St\nTotal: $45.67\nDate: 01/10/2026",
  "merchant_name": "Whole Foods Market",
  "total_amount": 45.67,
  "currency": "USD",
  "parsed_at": "2026-01-10T10:15:22Z",
  "error_message": null
}
```

OCR Status values
| Status      | Description                          |
|-------------|--------------------------------------|
| pending     | Not yet processed                    |
| processing  | OCR in progress                      |
| completed   | Successfully extracted and parsed    |
| failed      | OCR or parsing failed                |

Response 200 (failed case)
```json
{
  "receipt_id": "b1f3f2a8-0b8e-4d7f-9c2d-9c1d0e7b8b2a",
  "ocr_status": "failed",
  "ocr_text": null,
  "merchant_name": null,
  "total_amount": null,
  "currency": null,
  "parsed_at": "2026-01-10T10:15:22Z",
  "error_message": "Image too blurry, unable to extract text"
}
```

Errors
- 404 Not Found: receipt_id does not exist

Status codes
| Code | Meaning   |
|------|-----------|
| 200  | OK        |
| 404  | Not Found |

---

## 3. Data validation rules
### W01
- source_type must be one of: paper_receipt, app_screenshot, e_receipt_text
- Allowed file extensions: .jpg, .jpeg, .png
- Suggested max upload size (configurable): <= 10 MB
- purchase_date format: YYYY-MM-DD
- user_id should be a UUID string (for now can be a fixed seeded UUID)

### W02 (OCR fields)
- merchant_name: max 255 characters, alphanumeric + spaces and basic punctuation
- total_amount: positive decimal number, max 2 decimal places (e.g., 123.45)
- currency: ISO 4217 currency code (USD, EUR, GBP, etc.), default USD
- purchase_date: YYYY-MM-DD format, cannot be future date
- ocr_status: enum ['pending', 'processing', 'completed', 'failed']
- ocr_text: raw text extraction, no character limit (can be very long for receipts)

---

## 4. Receipt response schema evolution

### W01 Response
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "source_type": "string",
  "image_url": "string",
  "purchase_date": "date",
  "status": "string",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### W02 Response (extended)
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "source_type": "string",
  "image_url": "string",
  "purchase_date": "date",
  "status": "string",
  "ocr_status": "enum",
  "ocr_text": "string|null",
  "merchant_name": "string|null",
  "total_amount": "decimal|null",
  "currency": "string",
  "parsed_at": "timestamp|null",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

---

## 5. Minimal database expectations
### W01
- users table has at least one seeded user:
  - id = 00000000-0000-0000-0000-000000000001
- receipts table stores: id, user_id, source_type, image_url, purchase_date, status, timestamps

### W02 (new columns)
- receipts table extended with:
  - ocr_text (TEXT, nullable): raw OCR extracted text
  - ocr_status (ENUM, default 'pending'): processing status
  - merchant_name (VARCHAR(255), nullable): parsed merchant
  - total_amount (DECIMAL(10,2), nullable): parsed total
  - currency (VARCHAR(3), default 'USD'): currency code
  - parsed_at (TIMESTAMP, nullable): when OCR completed

---

## 6. Streamlit integration notes
### W01 Upload flow
1) User chooses file + purchase_date
2) Streamlit calls POST /receipts
3) On success, refresh receipts list by calling GET /receipts?user_id=...

Receipts list should show
- purchase_date
- status
- created_at
- receipt_id (shortened)

### W02 OCR flow
1) After upload success, optionally trigger OCR: POST /receipts/{id}/ocr
2) Poll GET /receipts/{id}/ocr-status to check status
3) Display OCR results in receipt detail view
4) Allow user to edit fields via PATCH /receipts/{id}

OCR Review/Edit UI should show
- Original receipt image (left side)
- Extracted fields (right side): merchant_name, total_amount, currency, purchase_date
- Edit form with validation
- OCR status badge
- Raw OCR text in collapsible section
 
