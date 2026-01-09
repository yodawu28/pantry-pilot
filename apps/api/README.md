# Pantry Pilot API

FastAPI backend for Pantry Pilot.

## Week 01 Features
- ✅ Health check endpoint
- ✅ Receipt upload (image → MinIO)
- ✅ Receipt CRUD (list, get by ID)
- ✅ PostgreSQL with SQLAlchemy async
- ✅ OpenAPI docs at `/docs`

## Development

```bash
# Install dependencies
cd apps/api
uv pip install -r pyproject.toml

# Run locally
uvicorn app.main:app --reload

# Run tests
pytest

# With Docker
docker build -t pantry-pilot-api .
docker run -p 8000:8000 pantry-pilot-api
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/receipts` | Upload receipt |
| GET | `/receipts?user_id=1` | List receipts |
| GET | `/receipts/{id}` | Get receipt details |

See full docs at `http://localhost:8000/docs`