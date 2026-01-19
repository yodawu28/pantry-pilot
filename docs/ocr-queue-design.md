# OCR Queue System Design

## Overview

Asynchronous queue system for processing receipt OCR in the background. Allows triggering OCR for all pending receipts without blocking API requests.

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌────────────┐      ┌─────────────┐
│   Web UI    │─────▶│   API        │─────▶│ OCR Queue  │─────▶│   Agent     │
│  (Streamlit)│      │  (FastAPI)   │      │  Service   │      │  Service    │
└─────────────┘      └──────────────┘      └────────────┘      └─────────────┘
                            │                     │                    │
                            │                     │                    │
                            ▼                     ▼                    ▼
                     ┌──────────────┐      ┌────────────┐      ┌─────────────┐
                     │  PostgreSQL  │      │   Memory   │      │    MinIO    │
                     │   Database   │      │   Queue    │      │   Storage   │
                     └──────────────┘      └────────────┘      └─────────────┘
```

## Components

### 1. OCRQueueService (`apps/api/app/services/ocr_queue.py`)

**Responsibilities:**
- Manage in-memory processing queue
- Track receipt processing status
- Trigger individual receipt OCR
- Batch process all pending receipts

**Key Methods:**
- `trigger_receipt_ocr(receipt_id, image_path, user_id, db)` - Process single receipt
- `process_all_pending(user_id, db, limit)` - Process all pending receipts for user
- `get_status(receipt_id)` - Get current status for receipt
- `clear_completed()` - Clean up completed/failed from memory

**Status Values:**
- `processing` - Currently being processed
- `completed` - Successfully processed
- `failed` - Processing failed

### 2. Repository Methods (`apps/api/app/repository/receipt_repository.py`)

**New Methods:**
- `get_pending_ocr_receipts(user_id, limit)` - Get all receipts with `ocr_status='pending'`
- `update_status(receipt_id, status, ocr_status)` - Update receipt status fields

### 3. API Endpoints (`apps/api/app/routers/receipts.py`)

#### POST `/receipts/ocr/process-all`
Trigger OCR processing for all pending receipts.

**Parameters:**
- `user_id` (int, default: 1) - User ID to process receipts for
- `limit` (int, optional) - Maximum number of receipts to process

**Response:**
```json
{
  "status": "queued",
  "message": "OCR processing queued for user 1",
  "user_id": 1,
  "limit": null
}
```

**Behavior:**
- Returns immediately (non-blocking)
- Processing happens in background using FastAPI BackgroundTasks
- Updates receipt `ocr_status` to "processing" → "completed"/"failed"

#### GET `/receipts/ocr/queue-status`
Get current queue status.

**Parameters:**
- `receipt_id` (int, optional) - Check specific receipt status

**Response (specific receipt):**
```json
{
  "receipt_id": 17,
  "status": "processing"
}
```

**Response (overall queue):**
```json
{
  "total_tracked": 25,
  "processing": 3,
  "completed": 20,
  "failed": 2
}
```

## Workflow

### 1. Upload Receipts
```bash
# Upload receipts via API/UI
POST /receipts
# Receipt created with ocr_status='pending'
```

### 2. Trigger Batch Processing
```bash
# Start processing all pending receipts
curl -X POST "http://localhost:8000/receipts/ocr/process-all?user_id=1"
```

### 3. Monitor Progress
```bash
# Check overall queue status
curl "http://localhost:8000/receipts/ocr/queue-status"

# Check specific receipt
curl "http://localhost:8000/receipts/ocr/queue-status?receipt_id=17"

# Get receipt details (includes ocr_status)
curl "http://localhost:8000/receipts/17"
```

### 4. View Results
```bash
# Get receipts list with extracted data
curl "http://localhost:8000/receipts?user_id=1"
```

## Processing Flow

```
1. User clicks "Process All" button
   ↓
2. API receives POST /receipts/ocr/process-all
   ↓
3. API adds task to BackgroundTasks queue
   ↓
4. API returns immediately with "queued" status
   ↓
5. Background worker starts processing:
   a. Fetch all pending receipts from DB
   b. For each receipt:
      - Mark as "processing" in DB
      - Add to in-memory queue
      - Call agent service asynchronously
      - Agent processes OCR extraction
      - Update receipt with results
   c. All tasks run concurrently with asyncio.gather()
   ↓
6. User can check status anytime via queue-status endpoint
   ↓
7. Completed receipts show in UI with extracted data
```

## Database Changes

### Receipt Status Flow

```
Initial:     ocr_status = 'pending'
             ↓
Queued:      ocr_status = 'processing'
             ↓
Success:     ocr_status = 'completed'
             (metadata + items saved)
             ↓
Failed:      ocr_status = 'failed'
             (error logged)
```

## Future Enhancements

### Phase 1 (Current - In-Memory Queue)
✅ In-memory queue with FastAPI BackgroundTasks
✅ Async processing with asyncio
✅ Status tracking in memory
✅ Simple and works for single-server deployments

### Phase 2 (Redis Queue)
- [ ] Add Redis for persistent queue
- [ ] Use RQ (Redis Queue) or Celery
- [ ] Survive server restarts
- [ ] Better for multi-worker deployments

### Phase 3 (Cloud Queue)
- [ ] AWS SQS or Google Cloud Tasks
- [ ] Fully managed queue service
- [ ] Auto-scaling workers
- [ ] Dead letter queue for failures

### Phase 4 (Advanced Features)
- [ ] Retry logic with exponential backoff
- [ ] Priority queue (urgent receipts first)
- [ ] Batch size limits and rate limiting
- [ ] Webhooks for completion notifications
- [ ] Real-time progress updates via WebSockets

## Usage Examples

### Process All Receipts
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/receipts/ocr/process-all",
        params={"user_id": 1, "limit": 10}
    )
    print(response.json())
```

### Check Queue Status
```python
import httpx

async with httpx.AsyncClient() as client:
    # Overall status
    response = await client.get(
        "http://localhost:8000/receipts/ocr/queue-status"
    )
    print(response.json())
    
    # Specific receipt
    response = await client.get(
        "http://localhost:8000/receipts/ocr/queue-status",
        params={"receipt_id": 17}
    )
    print(response.json())
```

### Streamlit UI Integration
```python
import streamlit as st
import requests

if st.button("🚀 Process All Pending Receipts"):
    response = requests.post(
        f"{API_URL}/receipts/ocr/process-all",
        params={"user_id": st.session_state.user_id}
    )
    if response.status_code == 200:
        st.success("✅ Processing started in background!")
        
        # Poll for status
        with st.spinner("Processing receipts..."):
            time.sleep(2)
            status = requests.get(f"{API_URL}/receipts/ocr/queue-status")
            st.json(status.json())
```

## Error Handling

### Network Errors
- Caught and logged in OCRQueueService
- Receipt marked as `ocr_status='failed'`
- Can retry manually via `/receipts/{id}/ocr/retry`

### Validation Errors
- Agent returns validation results
- Saved in receipt metadata
- UI shows warnings/errors to user

### Database Errors
- Transaction rolled back
- Receipt status unchanged
- Error logged for debugging

## Performance Considerations

### Current Implementation
- **Concurrent Processing**: Uses `asyncio.gather()` for parallel execution
- **Max Concurrency**: Limited by agent service capacity (~5-10 concurrent requests)
- **Memory Usage**: In-memory queue grows with pending receipts
- **Throughput**: ~10-20 receipts/minute (depends on agent response time)

### Optimization Tips
1. **Limit batch size**: Use `limit` parameter to process in chunks
2. **Monitor memory**: Call `clear_completed()` periodically
3. **Agent scaling**: Deploy multiple agent instances behind load balancer
4. **Database pooling**: Ensure adequate connection pool size

## Testing

```bash
# Start services
make up

# Upload test receipts
curl -X POST "http://localhost:8000/receipts" \
  -F "file=@receipt1.jpg" \
  -F "purchase_date=2026-01-19" \
  -F "user_id=1"

# Trigger batch processing
curl -X POST "http://localhost:8000/receipts/ocr/process-all?user_id=1"

# Check status
curl "http://localhost:8000/receipts/ocr/queue-status"

# View results
curl "http://localhost:8000/receipts?user_id=1"
```

## Configuration

### Environment Variables
```bash
# Agent service URL (in apps/api/.env)
AGENT_URL=http://agent:8002

# Database URL
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/pantry_pilot
```

### Timeout Settings
```python
# In OCRQueueService
httpx.AsyncClient(timeout=300.0)  # 5 minute timeout for agent calls
```

## Monitoring

### Logs
```bash
# API logs
docker logs -f pantry-pilot-api-1

# Agent logs  
docker logs -f pantry-pilot-agent-1

# Look for:
[OCR Queue] Found X pending receipts for user Y
[OCR Queue] ✓ Receipt 17 processed successfully
[OCR Queue] ✗ Receipt 18 failed: 500
[OCR Queue] Processing complete: {'total': 10, 'queued': 8, ...}
```

### Metrics to Track
- Total pending receipts
- Processing success rate
- Average processing time
- Queue depth
- Failed receipt count

## Security Considerations

1. **Authentication**: Add user authentication to endpoints
2. **Rate Limiting**: Prevent abuse of batch processing
3. **Authorization**: Verify user owns receipts being processed
4. **Input Validation**: Validate user_id and limit parameters
5. **Resource Limits**: Cap maximum batch size to prevent DoS

## Related Documentation
- [Agent Service Design](./agent-service-design.md)
- [MCP Tools Design](./mcp-tools-design.md)
- [API Contracts](./api-contracts.md)
- [Database Schema](./database-schema.md)
