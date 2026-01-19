#!/bin/bash
# Ollama entrypoint script with automatic model pulling

set -e

echo "🚀 Starting Ollama server..."

# Start Ollama in the background
ollama serve &
OLLAMA_PID=$!

# Give Ollama a moment to start binding to port
sleep 3

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
READY=0
for i in {1..60}; do
    # Check if process is still running
    if ! kill -0 $OLLAMA_PID 2>/dev/null; then
        echo "❌ Ollama process died unexpectedly"
        exit 1
    fi
    
    # Check if API is responding
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "✅ Ollama is ready!"
        READY=1
        break
    fi
    
    # Show progress
    if [ $((i % 10)) -eq 0 ]; then
        echo "   Still waiting... ($i/60)"
    fi
    
    sleep 2
done

if [ $READY -eq 0 ]; then
    echo "⚠️  Ollama API not responding after 120 seconds"
    echo "   Server process is running, continuing anyway..."
fi

# Check if model exists
MODEL_NAME="${OLLAMA_MODEL:-gemma3:4b}"
echo "🔍 Checking for model: $MODEL_NAME"

if ollama list 2>/dev/null | grep -q "$MODEL_NAME"; then
    echo "✅ Model $MODEL_NAME already exists"
else
    echo "📥 Pulling model $MODEL_NAME (this may take a while on first run)..."
    if ollama pull "$MODEL_NAME"; then
        echo "✅ Model $MODEL_NAME successfully pulled!"
    else
        echo "⚠️  Failed to pull model, but server is running"
        echo "   You can pull manually with: docker exec pantry-pilot-ollama ollama pull $MODEL_NAME"
    fi
fi

# List available models
echo "📋 Available models:"
ollama list 2>/dev/null || echo "   (models list not available yet)"

echo "✅ Ollama setup complete and ready!"
echo "   Server listening on port 11434"

# Keep the container running by waiting for the Ollama process
wait $OLLAMA_PID
