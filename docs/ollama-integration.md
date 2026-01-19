# Ollama + Gemma-3n Integration

## Overview

The agent service now uses **Ollama** to run the **Gemma-3n vision model** for receipt extraction.

## Architecture

```
Receipt Image → Agent Service → Ollama (Gemma-3n) → Extracted Data
```

## Setup

### Automated Setup (Recommended)

The Gemma-3n model is **automatically pulled** when you start Docker Compose:

```bash
# Start all services - Ollama will auto-pull the model on first run
docker-compose up -d

# Watch the logs to see model download progress
docker-compose logs -f ollama
```

**Note**: The first startup will take longer (several minutes) as it downloads the Gemma-3n model. Subsequent starts will be fast since the model is cached in the `ollama_data` volume.

### Verify Installation

```bash
# Check if model is available
docker exec pantry-pilot-ollama ollama list

# Should show:
# NAME              ID              SIZE      MODIFIED
# gemma3n:latest    xxxxx           x.xGB     x minutes ago
```

### Manual Model Management (Optional)

If you want to use a different model:

```bash
# Pull a specific model
docker exec pantry-pilot-ollama ollama pull <model-name>

# Or set in docker-compose.yml:
# environment:
#   OLLAMA_MODEL: your-model:tag
```

## Configuration

Edit `apps/agent/.env`:

```env
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=gemma3n:latest
GEMMA_TEMPERATURE=0.1
GEMMA_MAX_TOKENS=4096
```

## Testing

### Test Ollama directly:

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "gemma3n:latest",
  "prompt": "What is in this image?",
  "images": ["<base64-encoded-image>"]
}'
```

### Test Agent Extraction:

```bash
curl -X POST http://localhost:8002/extract \
  -H "Content-Type: application/json" \
  -d '{
    "receipt_id": 1,
    "image_path": "minio://receipts/test.jpg",
    "user_id": 1
  }'
```

## Model Specifications

- **Model**: Gemma-3n Vision
- **Provider**: Ollama
- **Capabilities**: Vision + Language understanding
- **Use Case**: Receipt text extraction, layout understanding
- **Temperature**: 0.1 (low for consistent extraction)
- **Max Tokens**: 4096
- **Storage**: 
  - Container path: `/root/.ollama/models`
  - Docker volume: `ollama_data`
  - Approximate size: 4-6GB

## Model Storage & Management

### Where Models Are Stored

**Inside Container:**
```
/root/.ollama/
├── models/           # Downloaded model files
│   └── manifests/
│   └── blobs/
└── history/          # Chat history
```

**On Host:**
- Docker volume name: `pantry-pilot_ollama_data`
- Managed by Docker at: `/var/lib/docker/volumes/pantry-pilot_ollama_data/_data`

### Check Model Storage

```bash
# List all models with sizes
docker exec pantry-pilot-ollama ollama list

# Check volume disk usage
docker system df -v | grep ollama

# Inspect volume details
docker volume inspect pantry-pilot_ollama_data

# Browse model files
docker exec pantry-pilot-ollama ls -lh /root/.ollama/models/
```

### Manage Models

```bash
# Pull additional models
docker exec pantry-pilot-ollama ollama pull llama2:latest

# Remove unused models
docker exec pantry-pilot-ollama ollama rm <model-name>

# Copy model from another source
docker cp /path/to/model pantry-pilot-ollama:/root/.ollama/models/
```

## Troubleshooting

### Ollama not responding

```bash
docker-compose restart ollama
docker logs pantry-pilot-ollama
```

### Model not found

```bash
docker exec pantry-pilot-ollama ollama pull gemma3n:latest
```

### Agent fails to connect

Check the `OLLAMA_URL` environment variable in the agent service matches the Ollama service name.

## Development Notes

- The agent includes a fallback to mock data if Ollama is unavailable
- Image preprocessing is applied before sending to Gemma
- JSON response is parsed with error handling for markdown code blocks
- Confidence scores are extracted from the model output
