# PantryPilot Roadmap (6 Weeks)

This roadmap is designed to be **easy to follow weekly**, with clear **deliverables**, **metrics**, and **GitHub-ready outputs**.

**Stack**: Streamlit + FastAPI + PostgreSQL + MinIO + Qdrant + Docker Compose

---

## Week 0 (1–2 days) — Repo & Infra Baseline
**Goal:** Run the full stack locally with a single command.

### Tasks
- Create repo structure:
  - `apps/streamlit/`
  - `services/api/`
  - `ml/`
  - `infra/`
  - `docs/`
- Add `infra/docker-compose.yml` with:
  - `postgres`, `qdrant`, `minio`, `api`, `streamlit`
- Add API endpoint `GET /health` → returns `{ "status": "ok" }`
- Add `.env.example` (no secrets)

### Deliverables (GitHub)
- `README.md` Quickstart:
  - `docker compose up`
  - local URLs (Streamlit, API docs, Qdrant, MinIO)
- Screenshot: Streamlit landing + API health response

### Metrics
- **Time-to-run**: clone → run successfully in **< 10 minutes** (self-test)

---

## Week 1 — Receipt Upload + Storage + DB Skeleton
**Goal:** Upload a receipt image and see it in a receipts list.

### Tasks
- DB: `users`, `receipts`
- API:
  - `POST /receipts` (multipart upload)
  - `GET /receipts?user_id=...`
  - `GET /receipts/{id}`
- MinIO:
  - upload object
  - store `image_url` in `receipts`
- Streamlit:
  - Upload screen (file uploader + purchase_date)
  - Receipts list screen

### Deliverables (GitHub)
- Demo GIF: upload → appears in list
- Example request/response in docs (or Swagger screenshots)

### Metrics
- Upload success rate: **100%** on **10** sample images

---

## Week 2 — OCR + Parse Line Items + Review/Edit UI
**Goal:** Parse receipt items into a table and let the user edit/save them.

### Tasks
- OCR pipeline:
  - preprocessing (crop/deskew/contrast)
  - OCR (PaddleOCR/EasyOCR)
- Parser:
  - group tokens/boxes → lines
  - detect “items block” (stop words: `TỔNG`, `CỘNG`, `VAT`, `THUẾ`, etc.)
  - extract `raw_name`, `qty/unit` (optional), `price` (optional), `confidence`
- DB: `receipt_items`
- API:
  - `POST /receipts/{id}/parse`
  - `GET /receipts/{id}/items`
  - `PUT /receipts/{id}/items` (batch update from UI)
- Streamlit:
  - Review screen with `st.data_editor` (add/edit/delete rows)
  - Save edits back to DB

### Deliverables (GitHub)
- 5–10 sample receipts + parsed output JSON (remove/blur PII if any)
- Short demo video: parse → edit → save

### Metrics
- Parse success rate: **>= 80%** on **20** receipt images
- Correction rate (rough): track how often users edit items

---

## Week 3 — Normalization + Inventory + Expiry Estimation
**Goal:** Confirm a receipt to update inventory and show expiring-soon items.

### Tasks
- DB: `food_catalog`, `inventory_items`
- Seed `food_catalog` with 200–500 common items
- Normalization (rule-based):
  - lowercase, remove diacritics, strip symbols
  - synonym dictionary
  - remove noise tokens (promo codes, store codes)
- Expiry estimation:
  - `expiry_estimated = purchase_date + default_shelf_life_days(category)`
  - allow user override
- API:
  - `POST /receipts/{id}/confirm` (normalize + inventory upsert)
  - `GET /inventory?user_id=...`
  - `PATCH /inventory/{item_id}` (override expiry, mark used/discarded)
- Streamlit:
  - Inventory screen
  - Filter “expiring soon” (<= N days)
  - Override expiry action

### Deliverables (GitHub)
- Screenshots: inventory view + expiring soon filter
- Doc snippet: “How expiry is estimated” (rules table by category)

### Metrics
- Normalization accuracy (manual spot-check): **>= 70%** on **50** items

---

## Week 4 — Recipe Ingest + Embeddings + Qdrant Search
**Goal:** Ingest recipes and retrieve top-k via Qdrant vector search.

### Tasks
- DB: `recipes` (metadata + ingredients_json + steps)
- Recipe ingest script (batch import)
- Embedding generator (choose one model, define vector dim D)
- Qdrant:
  - create collection: `pantrypilot_recipes_v1`
  - upsert points: `id=recipe_id`, vector, payload (`cuisine_tags`, `ingredients_norm`, etc.)
- API:
  - `POST /recipes/ingest`
  - `POST /vectors/recipes/reindex`
  - `GET /recommendations?user_id=...&top_k=...`
- Streamlit:
  - Recipes screen listing retrieved candidates

### Deliverables (GitHub)
- Script/notebook: ingest + reindex instructions
- Screenshot: recommended recipes list

### Metrics
- Retrieval feels smooth locally (no obvious lag)
- At least **1,000 recipes** (or smaller if MVP dataset is limited, but enough to demo)

---

## Week 5 — Ranking + Shopping List + Cook Flow
**Goal:** Recommendations are practical: prioritize expiring items + show missing ingredients.

### Tasks
- Ranking:
  - ingredient coverage (% available)
  - expiry priority boost
  - optional simplicity (time_minutes/difficulty)
- Missing ingredients:
  - compare `ingredients_norm` vs user inventory
- Shopping list screen:
  - checklist missing ingredients
  - optional export text
- “Cooked/Used” flow:
  - mark relevant inventory items as used (basic)

### Deliverables (GitHub)
- Demo video: choose recipe → shopping list → mark cooked
- README: ranking formula explanation

### Metrics
- Average top-10 coverage: **30–50%** (depends on inventory)
- Recommendations “make sense” in a recorded demo (qualitative)

---

## Week 6 — Evaluation + MLOps Baseline
**Goal:** Add evaluation harness + tracking so improvements are measurable.

### Tasks
- Gold set:
  - 50–100 receipt images
  - ground-truth items (a simple JSON format is fine)
- Evaluation scripts:
  - line item extraction: exact match and/or token F1
  - correction rate from user edits logs
- MLflow:
  - track parsing/normalization versions + metrics
- Monitoring baseline:
  - parse fail rate
  - correction rate trend

### Deliverables (GitHub)
- `ml/eval/` scripts + `README` (“How to run eval”)
- Metrics table in root `README.md` (v1 vs v2)

### Metrics
- Show at least one measurable improvement (v2 > v1) on one metric

---

## Optional Extensions (Post-Week 6)
Pick 2–3:
- Better receipt understanding: Layout-aware model (LayoutLM/Donut)
- `food_catalog` embedding + Qdrant matching for normalization
- Multi-store templates + format detection
- Meal planning weekly + user preferences
- Auth + multi-user with proper sessions

---

## Weekly Ritual (Recommended)
Create a short weekly devlog (GitHub Issue/Discussion):
- What shipped
- What broke
- Metrics snapshot
- Plan for next week