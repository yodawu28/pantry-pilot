# Queue Service

Standalone queue service using Redis Queue (RQ) for async task processing.

## Overview

This service provides a distributed, persistent queue for processing long-running tasks like OCR extraction. It's designed to be reusable across all Pantry Pilot services.

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌────────────┐
│   Client    │─────▶│    Redis     │◀─────│  Workers   │
│ (API/Web)   │      │    Queue     │      │ (RQ Workers)│
└─────────────┘      └──────────────┘      └────────────┘
                            │                      │
                            ▼                      ▼
                     Persistent Queue         Process Tasks
                                                   │
                                                   ▼
                                          ┌────────────┐
                                          │   Agent    │
                                          │  Service   │
                                          └────────────┘
```

## Features

✅ **Persistent**: Tasks survive service restarts  
✅ **Distributed**: Multiple workers can process tasks  
✅ **Reliable**: Automatic retry and failure handling  
✅ **Scalable**: Add/remove workers dynamically  
✅ **Observable**: Track job status and queue metrics  
✅ **Reusable**: Use from any service (API, Web, Agent)  

## Components

### 1. Queue Client (`pantry_queue/client.py`)
Enqueue tasks and check status

### 2. Tasks (`pantry_queue/tasks/ocr_tasks.py`)
Task definitions (what workers execute)

### 3. Workers (`pantry_queue/workers/worker.py`)
Worker processes that consume tasks

### 4. Config (`pantry_queue/config.py`)
Settings and configuration

## Quick Start (Local Development)

### 1. Start Redis
```bash
docker-compose up -d redis
```

### 2. Start Worker
```bash
# macOS requires this env var to avoid fork() crashes
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

# From project root
source .venv/bin/activate
PYTHONPATH=apps/queue rq worker pantry-pilot --url redis://localhost:6379 -v
```

### 3. Start API (if not running)
```bash
cd apps/api && uvicorn app.main:app --reload --port 8000
```

### 4. Start Agent (if not running)
```bash
cd apps/agent && uvicorn app.main:app --reload --port 8002
```

### 5. Trigger OCR Processing
```bash
# Process all pending receipts
curl -X POST "http://localhost:8000/receipts/ocr/process-all?user_id=1&limit=5"

# Check queue status
curl "http://localhost:8000/receipts/ocr/queue-status"
```

## Usage

### From API Service

The API service has a simple queue client built-in:

```python
# apps/api/app/services/queue_client.py
from app.services.queue_client import simple_queue_client

# Enqueue single task
job_id = simple_queue_client.enqueue_ocr_task(
    receipt_id=17,
    image_path="minio://receipts/abc123.jpg",
    user_id=1
)

# Get queue info
info = simple_queue_client.get_queue_info()
```

### Running Workers

```bash
# Single worker (local)
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES  # macOS only
PYTHONPATH=apps/queue rq worker pantry-pilot --url redis://localhost:6379

# Multiple workers (for scaling)
PYTHONPATH=apps/queue rq worker pantry-pilot --url redis://localhost:6379 --name worker-1 &
PYTHONPATH=apps/queue rq worker pantry-pilot --url redis://localhost:6379 --name worker-2 &
```

### Via Docker

```bash
# Start Redis + Workers
docker-compose up redis queue-worker
```

## Environment Variables

```bash
# Redis connection (local)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Redis connection (Docker)
REDIS_HOST=redis

# Queue settings
QUEUE_NAME=pantry-pilot
DEFAULT_TIMEOUT=600
RESULT_TTL=3600
FAILURE_TTL=86400

# Services (local)
AGENT_URL=http://localhost:8002
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pantry_pilot

# Services (Docker)
AGENT_URL=http://agent:8002
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/pantry_pilot

# Worker
WORKER_NAME=worker-1
BURST_MODE=false
```

# Queue settings
QUEUE_NAME=pantry-pilot
DEFAULT_TIMEOUT=600
RESULT_TTL=3600
FAILURE_TTL=86400

# Services
AGENT_URL=http://agent:8002
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/pantry_pilot

# Worker
WORKER_NAME=worker-1
BURST_MODE=false
```

## Task Flow

```
1. Client enqueues task
   ↓
2. Task stored in Redis queue
   ↓
3. Worker picks up task
   ↓
4. Worker executes task function
   ↓
5. Result stored in Redis
   ↓
6. Client checks result
```

## Job States

- `queued` - Waiting to be processed
- `started` - Currently being processed
- `finished` - Completed successfully
- `failed` - Completed with error
- `deferred` - Waiting for dependency
- `scheduled` - Scheduled for future execution
- `canceled` - Manually canceled

## Monitoring

```python
# Queue stats
info = queue_client.get_queue_info()
# {
#   "count": 5,              # Pending
#   "started_jobs": 2,       # Processing
#   "finished_jobs": 100,    # Completed
#   "failed_jobs": 3,        # Failed
# }

# Job status
status = queue_client.get_job_status("ocr-17")
# {
#   "job_id": "ocr-17",
#   "status": "finished",
#   "result": {...},
#   "started_at": "2026-01-19T10:30:00",
#   "ended_at": "2026-01-19T10:31:23"
# }
```

## Error Handling

### Automatic Retry
```python
# Task will retry on failure (configured in RQ)
job = queue.enqueue(
    task_func,
    retry=Retry(max=3, interval=[10, 30, 60])
)
```

### Failed Jobs
```python
# Clear failed jobs
cleared = queue_client.clear_failed_jobs()

# Or inspect failures
from rq import Queue
from redis import Redis

conn = Redis()
q = Queue('pantry-pilot', connection=conn)
failed_registry = q.failed_job_registry

for job_id in failed_registry.get_job_ids():
    job = Job.fetch(job_id, connection=conn)
    print(f"Failed: {job.exc_info}")
```

## Scaling

### Horizontal Scaling
```bash
# Add more workers on different machines
docker-compose scale queue-worker=5
```

### Priority Queues
```python
# High priority queue
queue_client.enqueue_ocr_task(
    receipt_id=17,
    image_path="...",
    user_id=1,
    priority="high"  # Goes to front of queue
)
```

## Development

```bash
# Install dependencies
cd apps/queue
uv pip install -e .

# Run tests
pytest

# Format code
black pantry_queue/
ruff check pantry_queue/

# Run worker locally (from project root)
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES  # macOS only
source .venv/bin/activate
PYTHONPATH=apps/queue rq worker pantry-pilot --url redis://localhost:6379 -v

# Clear queue (useful for debugging)
redis-cli -h localhost -p 6379 FLUSHALL

# Check queue status
source .venv/bin/activate
rq info --url redis://localhost:6379
```

## Troubleshooting

### macOS Fork Error
If you see `objc[...]: +[NSMutableString initialize] may have been in progress...`:
```bash
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
```

### Redis Connection Refused
```bash
# Start Redis
docker-compose up -d redis

# Or check if running
docker ps | grep redis
```

### Worker Not Processing Jobs
```bash
# Check if worker is running
rq info --url redis://localhost:6379

# Should show:
# 1 workers, 1 queues
```

### Jobs Failing
```bash
# Check failed jobs
source .venv/bin/activate
python << 'EOF'
from redis import Redis
r = Redis(host='localhost', port=6379)
failed_keys = r.keys('rq:job:*')
for key in failed_keys[:3]:
    job_data = r.hgetall(key)
    if b'exc_info' in job_data:
        print(f"Job: {key.decode()}")
        print(f"Error: {job_data[b'exc_info'].decode()[:500]}")
        print("---")
EOF
```

## Production Considerations

1. **Worker Count**: Start with 2-5 workers, scale based on load
2. **Redis Persistence**: Enable AOF or RDB snapshots
3. **Monitoring**: Use RQ dashboard or custom metrics
4. **Timeouts**: Set appropriate task timeouts (default: 600s)
5. **Memory**: Monitor Redis memory usage
6. **Health Checks**: Ping Redis and check worker status

## Integration with Other Services

### API Service
The API has built-in endpoints for queue operations:

```bash
# Process all pending receipts
POST /receipts/ocr/process-all?user_id=1&limit=10

# Check queue status
GET /receipts/ocr/queue-status

# Check job status
GET /receipts/ocr/job/{job_id}
```

### Web UI
```python
# apps/web/app/views/receipts.py
import requests

if st.button("Process All"):
    response = requests.post(
        f"{API_URL}/receipts/ocr/process-all",
        params={"user_id": user_id, "limit": 10}
    )
    result = response.json()
    st.success(f"Queued {result['queued']} receipts")
```

## Comparison: Before vs After

### Before (In-Memory)
- ❌ Lost on restart
- ❌ Single server only
- ❌ No persistence
- ❌ Limited observability
- ✅ Simple setup

### After (Redis Queue)
- ✅ Persists on restart
- ✅ Distributed workers
- ✅ Persistent storage
- ✅ Full observability
- ✅ Production-ready
- ✅ Reusable across services

## Related Documentation
- [RQ Documentation](https://python-rq.org/)
- [OCR Queue Design](../../docs/ocr-queue-design.md)
- [Architecture](../../docs/architecture.md)
