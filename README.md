# 🥘 Pantry Pilot

Smart pantry management system with receipt OCR, expiration tracking, and recipe suggestions.

## Stack

- **Backend**: FastAPI + Python 3.11
- **Frontend**: Streamlit
- **Database**: PostgreSQL 16
- **Storage**: MinIO (S3-compatible)
- **Vector DB**: Qdrant
- **Package Manager**: uv

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- uv (optional for local dev)

### Run All Services

```bash
# Clone repo
git clone <repo-url>
cd pantry-pilot

# Start all services
docker compose up --build

# Access:
# - Streamlit:      http://localhost:8501
# - API Docs:       http://localhost:8000/docs
# - MinIO Console:  http://localhost:9001 (minioadmin/minioadmin)
# - Qdrant:         http://localhost:6333/dashboard
```

---

## Week 01 (2026-W01) ✅

**Theme**: Receipt Upload + Storage + DB Skeleton

### Completed Tasks
- [x] Boot all services with `docker compose up`
- [x] Upload receipt image from Streamlit → save to MinIO
- [x] Save receipt metadata to Postgres
- [x] Display receipts list in Streamlit
- [x] API docs at `/docs`

### Demo Checklist
- [x] `docker compose up` runs all services
- [x] Upload 1 receipt via Streamlit
- [x] See receipt in list
- [x] API docs accessible at `http://localhost:8000/docs`

---

## Project Structure

```
pantry-pilot/
├── apps/
│   ├── api/           # FastAPI backend
│   └── web/           # Streamlit frontend
├── infra/
│   └── postgres/      # DB init scripts
├── docs/
│   ├── plans/         # Weekly plans
│   ├── architecture.md
│   └── api-contracts.md
├── docker-compose.yml
└── README.md
```

---

## Development

### Local API Development

```bash
cd apps/api

# Install deps with uv
uv pip install -r pyproject.toml

# Run locally (requires Postgres + MinIO running)
uvicorn app.main:app --reload

# Run tests
pytest

# Lint
ruff check .
black .
```

### Local Web Development

```bash
cd apps/web

uv pip install -r pyproject.toml
streamlit run app/main.py
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/receipts` | Upload receipt (multipart) |
| `GET` | `/receipts?user_id=1` | List receipts for user |
| `GET` | `/receipts/{id}` | Get receipt details |

See full interactive docs: **http://localhost:8000/docs**

---

## Environment Variables

Copy `.env.example` to `.env` and customize if needed.

Key variables:
- `DATABASE_URL`: Postgres connection string
- `MINIO_ENDPOINT`: MinIO server address
- `QDRANT_URL`: Qdrant server address
- `API_URL`: API base URL (for Streamlit)

---

## Next Steps (W02)

- [ ] OCR integration (Textract/Tesseract)
- [ ] Parse receipt items
- [ ] Store items in Postgres
- [ ] Display items in Streamlit

---

## License

MIT