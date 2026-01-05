# Technical Proposal — Receipt-to-Meal Planner (Streamlit + FastAPI + Qdrant, AI + MLOps)

## 1) Problem
Người dùng mua nhiều thực phẩm nhưng:
- Quên hạn sử dụng → bỏ đi lãng phí.
- Không biết nấu gì từ những gì đã mua; phải tự tìm recipe và hay thiếu nguyên liệu.

## 2) Solution Overview
Hệ thống end-to-end:
1) Nhập hóa đơn (ảnh hóa đơn giấy / ảnh chụp e-receipt trên app)  
2) OCR + trích xuất line items (tên hàng, số lượng/khối lượng nếu có)  
3) Chuẩn hóa tên hàng → map về danh mục thực phẩm (taxonomy)  
4) Tạo inventory theo thời gian + ước lượng hạn dùng theo loại thực phẩm  
5) Gợi ý recipe ưu tiên dùng đồ sắp hết hạn + shopping list các nguyên liệu thiếu  
6) Human-in-the-loop: user xác nhận/sửa → tạo dữ liệu huấn luyện & cải thiện dần

**Vector Search**: dùng **Qdrant** để lưu embeddings & query similarity cho recipes (và có thể cho food_catalog).

## 3) MVP Scope

### In-scope (MVP)
- **Streamlit UI**
  - Upload ảnh hóa đơn
  - Review/confirm/sửa line items (table editor)
  - Inventory + filter “sắp hết hạn”
  - Recipe recommendations + missing ingredients
- **FastAPI Backend**
  - CRUD receipts, items, inventory
  - Endpoint parse OCR
  - Endpoint recommend recipes
  - Endpoint ingest recipes (batch) + push embeddings lên Qdrant
- **OCR**: PaddleOCR/EasyOCR + parsing heuristics
- **Normalization**: rule + (optional) embedding match (Qdrant) để map raw_name → canonical
- **Expiry estimation** theo category + user override
- **Recipe retrieval**: Qdrant vector search + ranking + shopping list
- Data logging cho corrections để tạo dataset nội bộ

### Out-of-scope (MVP)
- Nhận diện hạn dùng chính xác từ bao bì sản phẩm
- Tự động sync từ mọi app siêu thị
- Meal plan nâng cao (calories/macro, khẩu phần)
- Tích hợp mua hàng online/đặt hàng

## 4) System Architecture

### 4.1 Components
- **UI App**: Streamlit (`apps/streamlit`)
- **API**: FastAPI (`services/api`)
- **DB**: PostgreSQL (business data)
- **Vector DB**: Qdrant (recipe embeddings + payload filters)
- **Object Storage**: MinIO/S3 lưu ảnh hóa đơn
- **MLOps (optional)**: MLflow + DVC + scheduler/worker (Prefect/Cron)

### 4.2 Data flow (MVP)
1) Streamlit upload image → API `POST /receipts` → lưu ảnh MinIO + tạo receipt record
2) Parse → API `POST /receipts/{id}/parse`:
   - preprocess → OCR → parse line items → lưu `receipt_items`
3) Review/edit → API `PUT /receipts/{id}/items`
4) Confirm → API `POST /receipts/{id}/confirm`:
   - normalize → update `inventory_items` + expiry estimate
5) Recommend → API `GET /recommendations`:
   - build query vector từ inventory
   - Qdrant search top-k recipes (có filter cuisine_tags nếu cần)
   - rank theo coverage + expiry priority
   - trả recipes + missing ingredients

## 5) Qdrant Design

### 5.1 Collections (suggested)
- `recipes_v1`
  - **point_id**: dùng `recipe_id` (UUID) dạng string (nếu môi trường bạn không support UUID point_id thì lưu mapping table trong Postgres)
  - vector: embedding(D)
  - payload:
    - `title`: string
    - `cuisine_tags`: array[string]
    - `ingredients_norm`: array[string] (tên ingredient đã normalize)
    - `source`: string (dataset/source)
    - `updated_at`: timestamp (optional)

- (Optional) `food_catalog_v1`
  - point_id: `food_id`
  - payload: `canonical_name`, `category`, `aliases`

### 5.2 Filtering strategy
- Filter theo `cuisine_tags` / `difficulty` / `time_minutes` (nếu có)
- Khi rank “coverage”, ta vẫn cần ingredients từ Postgres (`recipes.ingredients_json`) hoặc để sẵn `ingredients_norm` trong payload để tính nhanh.

> MVP đơn giản: Qdrant trả top-k recipe_id; API fetch full recipe từ Postgres để tính coverage + missing ingredients chính xác.

## 6) API Design (MVP)
### Receipts
- `POST /receipts`
- `POST /receipts/{id}/parse`
- `PUT /receipts/{id}/items`
- `POST /receipts/{id}/confirm`

### Inventory
- `GET /inventory?user_id=...`
- `PATCH /inventory/{item_id}` (override expiry, mark used/discarded)

### Recipes / Vectors
- `POST /recipes/ingest` (batch insert recipes metadata vào Postgres)
- `POST /vectors/recipes/reindex` (embed + upsert Qdrant)  
- `GET /recommendations?user_id=...&top_k=10&cuisine=...`

## 7) OCR & Parsing Design (MVP)
- Preprocess: crop, deskew, denoise, contrast
- OCR: PaddleOCR/EasyOCR
- Parse: group lines + heuristic “items block”
- Human-in-the-loop: Streamlit table editor

## 8) Normalization
- Rule-based: bỏ dấu, remove noise tokens, synonym dict
- Optional embedding-match qua Qdrant (`food_catalog_v1`) để gợi ý canonical tốt hơn

## 9) Expiry Estimation (pragmatic)
- expiry_estimated = purchase_date + default_shelf_life_days(category)
- user override expiry

## 10) Recommendation & Ranking
- Retrieve: Qdrant vector search top-k
- Rank: coverage + expiry priority + simplicity
- Output: recipes + explanation + missing ingredients + shopping list

## 11) MLOps Plan
- Log: images, OCR raw, parsed items, user corrections
- Gold set: 100 receipts regression
- MLflow: track experiments parsing/normalization
- CI: unit + integration tests, docker build

## 12) Security & Privacy
- receipt images private (signed URL/proxy)
- delete data supported
- isolate by user_id

## 13) Repo Structure
- `apps/streamlit/`
- `services/api/`
- `ml/`
- `infra/` (docker-compose: api + postgres + qdrant + minio)
- `docs/`

## 14) Milestones
- M1: Upload + storage + Streamlit screens
- M2: OCR parse + review/edit
- M3: Normalization + inventory + expiry
- M4: Recipe ingest + Qdrant vector search + ranking + shopping list
- M5: MLOps baseline (gold set + eval + monitoring)