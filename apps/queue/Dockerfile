FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy shared package first
COPY packages/shared /shared
RUN pip install -e /shared

# Copy queue service
COPY apps/queue/pyproject.toml .
COPY apps/queue/pantry_queue ./pantry_queue

# Install dependencies
RUN pip install --no-cache-dir -e .

# Run worker
CMD ["python", "-m", "pantry_queue.workers.worker"]
