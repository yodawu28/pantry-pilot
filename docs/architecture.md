# Architecture (Qdrant-first)

## 1) Overview
MVP gồm:
- Streamlit UI
- FastAPI backend
- Postgres (business data)
- Qdrant (vectors + payload filters)
- MinIO/S3 (receipt images)
- Optional: MLflow + worker/scheduler

---

## 2) Component Diagram (Mermaid)

![Architecture Diagram](images/diagram_1.png)

## 3) Sequence Diagram — Receipt Upload → Parse → Review → Confirm
![Sequence Diagram](images/diagram_2.png)

## 4) Sequence Diagram — Recipe Ingest → Embed → Qdrant Upsert
![Sequence Diagram](images/diagram_3.png)

5) Sequence Diagram — Recommend Recipes
![Sequence Diagram](images/diagram_4.png)