# API Contracts — PantryPilot (W01)

This document defines the request/response contracts for Week 1 (W01).

Scope
- Healthcheck
- Receipts upload
- Receipts listing and detail

Base URL
- Local: http://localhost:8000

Notes
- Auth is out of scope for W01. Use a placeholder user_id (seeded user).
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

## 3. Data validation rules (W01)
- source_type must be one of: paper_receipt, app_screenshot, e_receipt_text
- Allowed file extensions: .jpg, .jpeg, .png
- Suggested max upload size (configurable): <= 10 MB
- purchase_date format: YYYY-MM-DD
- user_id should be a UUID string (for now can be a fixed seeded UUID)

---

## 4. Minimal database expectations (W01)
- users table has at least one seeded user:
  - id = 00000000-0000-0000-0000-000000000001
- receipts table stores: id, user_id, source_type, image_url, purchase_date, status, timestamps

---

## 5. Streamlit integration notes (W01)
Upload flow
1) User chooses file + purchase_date
2) Streamlit calls POST /receipts
3) On success, refresh receipts list by calling GET /receipts?user_id=...

Receipts list should show
- purchase_date
- status
- created_at
- receipt_id (shortened)
 
