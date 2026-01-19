#!/bin/bash
# Setup script for Ollama and Gemma-3n model

set -e

echo "🚀 Setting up Ollama with Gemma-3n vision model..."

# Start Ollama service
echo "📦 Starting Ollama container..."
docker-compose up -d ollama

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "✅ Ollama is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Ollama not responding after 60 seconds"
        echo "   Check logs with: docker-compose logs ollama"
        exit 1
    fi
    echo "   Waiting... ($i/30)"
    sleep 2
done

# Pull gemma3:4b model
MODEL_NAME="${1:-gemma3:4b}"
echo "📥 Pulling model: $MODEL_NAME"
echo "   (This may take several minutes on first run)"
docker exec pantry-pilot-ollama ollama pull "$MODEL_NAME"

# Verify
echo ""
echo "📋 Available models:"
docker exec pantry-pilot-ollama ollama list

echo ""
echo "✅ Setup complete!"
echo "   Ollama is running at: http://localhost:11434"
echo "   Model $MODEL_NAME is ready for use"
