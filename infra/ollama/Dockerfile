FROM ollama/ollama:latest

# Copy custom entrypoint
COPY infra/ollama/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set default model to pull
ENV OLLAMA_MODEL=minicpm-v

# Use custom entrypoint
ENTRYPOINT ["/entrypoint.sh"]
