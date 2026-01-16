# Agent Module

LLM agent for receipt extraction using OpenAI GPT-4o vision model + MCP tools.

## Features

- 🖼️ Vision model integration (GPT-4o)
- 🛠️ MCP tool calling (get image, validate, context)
- 🔍 Image preprocessing (contrast, denoise, resize)
- ✅ Validation pipeline
- 📊 Context-aware extraction

## Architecture

```
┌──────────────┐
│ Receipt Agent│
└──────┬───────┘
       │
       ├─▶ MCP: ocr-text (EasyOCR)
       ├─▶ MCP: get-image
       ├─▶ Vision: preprocess image
       ├─▶ OpenAI GPT-4o: extract data
       ├─▶ MCP: validate
       └─▶ Return JSON (API saves to DB)
```

## Configuration

Add your OpenAI API key to `.env`:

```bash
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o
```

## Endpoints

- `POST /extract` - Extract receipt data
- `GET /extract/{id}/status` - Check processing status
- `POST /extract/{id}/retry` - Retry failed extraction

## Development

```bash
cd apps/agent
uv pip install -e .

# Run locally
uvicorn app.main:app --reload --port 8002
```
- [ ] Add retry logic with exponential backoff
- [ ] Implement progress tracking (for long extractions)
- [ ] Add caching for repeated extractions
- [ ] Performance benchmarking

## Testing

```bash
pytest tests/ -v
```

Access: http://localhost:8002/docs