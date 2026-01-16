# Quick Start with Automated Ollama Setup

## Start Everything (Includes Auto Model Pull)

```bash
# Clone and navigate to project
cd pantry-pilot

# Start all services (Ollama will auto-pull Gemma-3n on first run)
docker-compose up -d

# Watch Ollama setup progress (first time only - takes a few minutes)
docker-compose logs -f ollama

# When you see "✅ Ollama setup complete and ready!", press Ctrl+C
```

## What Happens Automatically

1. **Ollama starts** and begins serving on port 11434
2. **Checks for Gemma-3n model** in the cache (`/root/.ollama` in container)
3. **Downloads the model** if not present (only on first run)
4. **Caches the model** in the `ollama_data` Docker volume
5. **Agent service** waits for Ollama to be healthy
6. **System is ready** for receipt extraction

## Model Storage Location

**Inside Container:**
- Path: `/root/.ollama/models`
- This is where Ollama stores all downloaded models

**On Host Machine:**
- Docker Volume: `ollama_data`
- Location: Managed by Docker (typically `/var/lib/docker/volumes/pantry-pilot_ollama_data/_data`)
- Size: ~4-6GB for Gemma-3n model

**Inspect Volume:**
```bash
# View volume details
docker volume inspect pantry-pilot_ollama_data

# Check volume size
docker system df -v | grep ollama_data

# List models in the volume
docker exec pantry-pilot-ollama ls -lh /root/.ollama/models/

# View all models with sizes
docker exec pantry-pilot-ollama ollama list
```

## First Run vs Subsequent Runs

### First Run (5-10 minutes)
- Ollama downloads Gemma-3n model (~4-6GB)
- All services start and wait for dependencies
- Total time: ~5-10 minutes depending on internet speed

### Subsequent Runs (<30 seconds)
- Model already cached in volume
- Services start immediately
- Total time: ~20-30 seconds

## Verify Setup

```bash
# Check all services are healthy
docker-compose ps

# Verify Gemma-3n is available
docker exec pantry-pilot-ollama ollama list

# Test agent endpoint
curl http://localhost:8002/health
```

## Monitoring First Setup

```bash
# Follow Ollama logs to see model download
docker-compose logs -f ollama

# You'll see:
# 🚀 Starting Ollama server...
# ⏳ Waiting for Ollama to be ready...
# ✅ Ollama is ready!
# 🔍 Checking for model: gemma3n:latest
# 📥 Pulling model gemma3n:latest (this may take a while on first run)...
# [Download progress...]
# ✅ Model gemma3n:latest successfully pulled!
# ✅ Ollama setup complete and ready!
```

## Changing Models

Edit `docker-compose.yml` to use a different model:

```yaml
ollama:
  environment:
    OLLAMA_MODEL: llama2:latest  # or any other Ollama model
```

Then restart:
```bash
docker-compose restart ollama
```

## Troubleshooting

### Download Interrupted
```bash
# Restart Ollama - it will resume the download
docker-compose restart ollama
```

### Clean Start (Re-download Model)
```bash
# Remove model cache and restart (WARNING: This deletes the model!)
docker-compose down -v
docker-compose up -d

# Or just remove Ollama volume specifically
docker volume rm pantry-pilot_ollama_data
docker-compose up -d ollama
```

### Backup/Export Model
```bash
# Create backup of the volume
docker run --rm -v pantry-pilot_ollama_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/ollama-models-backup.tar.gz -C /data .

# Restore from backup
docker run --rm -v pantry-pilot_ollama_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/ollama-models-backup.tar.gz -C /data
```

### Move to Different Model Storage Location
```bash
# Stop services
docker-compose down

# Copy volume data to host directory
mkdir -p ./data/ollama
docker run --rm -v pantry-pilot_ollama_data:/from -v $(pwd)/data/ollama:/to \
  alpine sh -c "cp -r /from/* /to/"

# Update docker-compose.yml to use bind mount instead:
# volumes:
#   - ./data/ollama:/root/.ollama

# Restart
docker-compose up -d
```

### Check Disk Space
The Gemma-3n model requires ~4-6GB. Check available space:
```bash
df -h
```
