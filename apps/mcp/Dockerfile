FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy shared package first
COPY packages/shared /packages/shared
WORKDIR /packages/shared
RUN uv pip install --system .

# Back to mcp
WORKDIR /app
COPY apps/mcp/pyproject.toml ./
RUN uv pip install --system -r pyproject.toml

# Copy app code
COPY apps/mcp/app ./app

# Expose port
EXPOSE 8001

# Run MCP server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
