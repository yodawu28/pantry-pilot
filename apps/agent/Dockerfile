FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

# Copy shared package
COPY packages/shared /packages/shared
WORKDIR /packages/shared
RUN uv pip install --system .

# Back to agent
WORKDIR /app
COPY apps/agent/pyproject.toml ./
RUN uv pip install --system -r pyproject.toml

COPY apps/agent/app ./app

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]