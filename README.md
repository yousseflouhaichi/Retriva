## RAG Project (backend-first scaffold)

### Prereqs
- Python 3.13
- `uv`
- Docker Desktop

### Start infrastructure

```bash
docker compose up -d
```

### Configure environment
- Copy `.env.example` to `.env` and fill in keys as needed.

### Run the API

```bash
uv run uvicorn backend.main:app --reload --port 8080
```

Health check:
- `GET /health`

Workspaces (for the UI dropdown): Qdrant collections named `company_*` are listed by
- `GET /workspaces` (returns JSON `{"workspaces": ["id", ...]}` sorted; id is the suffix after `company_`)

System status (dependency checks and non-secret model metadata for dashboards):
- `GET /status`

Document index (per workspace, from Qdrant chunk payloads; may truncate on very large corpora):
- `GET /documents?company_id=demo`

Workspace UI preferences (per `company_id`, stored in Redis; no auth yet):
- `GET /workspace/preferences?company_id=demo`
- `PATCH /workspace/preferences?company_id=demo` with JSON body (partial fields: `theme`, `density`, `show_streaming_indicator`)

### Run the ARQ worker (separate terminal)

```bash
uv run arq backend.workers.ingestion_worker.WorkerSettings
```

### Try ingestion
- Set `OPENAI_API_KEY` in `.env` (embeddings are required for indexing).
- `POST /ingest/upload?company_id=demo` with multipart form file `file`
- Poll `GET /ingest/status/{job_id}` until `ready` (response includes `chunks_indexed` when using the JSON status format)

### Try streaming query
- Set `OPENAI_API_KEY` and **`COHERE_API_KEY`** in `.env` (transform, retrieval rerank, and answer generation).
- Ingest at least one document for `company_id` first so Qdrant and the Redis BM25 corpus are populated.
- `POST /query/stream` with JSON `{ "company_id": "demo", "question": "your question" }`
- SSE events: `sources` (JSON array of previews), then `token` chunks, then `done`. On failure, `error` then `done`.

### Frontend (Vite + React + Tailwind)

- Copy `frontend/.env.example` to `frontend/.env` and set **`VITE_API_URL`** to your API base (no trailing slash), e.g. `http://127.0.0.1:8080`.
- Install and run:

```bash
cd frontend
npm install
npm run dev
```

- Open the printed local URL (default port **5173**). CORS is enabled for that origin in `backend/main.py`.
- Use **Workspace** for `company_id`, **Upload** for ingestion (polls status every 2s), **Chat** for streaming queries via **`useSSE`**.
