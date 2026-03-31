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

### Run the ARQ worker (separate terminal)

```bash
uv run arq backend.workers.ingestion_worker.WorkerSettings
```

### Try ingestion
- Set `OPENAI_API_KEY` in `.env` (embeddings are required for indexing).
- `POST /ingest/upload?company_id=demo` with multipart form file `file`
- Poll `GET /ingest/status/{job_id}` until `ready` (response includes `chunks_indexed` when using the JSON status format)

### Try streaming query
- `POST /query/stream` with JSON `{ "company_id": "demo", "question": "hello" }`
- Response is SSE events (`meta`, `token`, `done`)
