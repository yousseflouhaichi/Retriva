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
- Python dependencies are pinned in `uv.lock`; use `uv sync --frozen` in CI and Docker for reproducible installs.
- Document parsing uses the **Unstructured HTTP API** (Docker Compose service). The backend does not import the `unstructured` Python package; keep the Unstructured container running for ingestion.

### CI / CD
- **CI** (`.github/workflows/ci.yml`): on pushes and pull requests to `main`, runs `pytest` and `frontend` tests + production build (`VITE_API_URL=/api`), uploads the `frontend/dist` artifact as `frontend-dist`.
- **Deploy** (`.github/workflows/deploy.yml`): after a successful CI run on `main` or `master` (push only), rsyncs the static site to `/var/www/rag` on your server and runs `git pull` + `docker compose -f deploy/docker-compose.prod.yml ... up -d --build`. Configure GitHub repository secrets per [DEPLOY.md](DEPLOY.md).

### Production / demo deploy
- Full steps, Oracle VM, Caddy, and secrets are documented in **[DEPLOY.md](DEPLOY.md)**.
- **Demo warning:** there is no end-user authentication; a public URL will consume your API provider quotas. Keep dependency containers off the public internet (the sample Compose binds the API to `127.0.0.1:8080` only).

### Run the API

```bash
uv run uvicorn backend.main:app --reload --port 8080
```

Health check:
- `GET /health`

Workspaces (for the UI dropdown): Qdrant collections whose names are valid workspace ids (letters, digits, `-`, `_`) are listed by
- `GET /workspaces` (returns JSON `{"workspaces": ["id", ...]}` sorted). Legacy collections named `company_{id}` still appear as `id`.
- `POST /workspaces` with JSON `{"workspace_id": "your-id"}` creates an empty Qdrant collection when missing (same id rules as ingest). Response: `{"workspace_id": "...", "created": true|false}`.
- `DELETE /workspaces/{workspace_id}` removes the Qdrant collection and related Redis keys (BM25 corpus, workspace preferences). Returns **204** when done (idempotent if the collection is already gone).

New data is stored under the plain id collection (for example `demo`, not `company_demo`). If you still have vectors only under `company_{id}`, migrate or re-ingest into the plain-named collection.

System status (dependency checks, non-secret model metadata, and ARQ ingestion queue snapshot):
- `GET /status` (includes `ingestion_worker`: queue depth and worker heartbeat from Redis)

Document index (per workspace, from Qdrant chunk payloads; may truncate on very large corpora):
- `GET /documents?company_id=demo&limit=100&offset=0` (each row includes `chunk_count` and optional `last_indexed_at` for chunks ingested after this release)
- `DELETE /documents?company_id=demo&document_name=...` deletes all points whose payload `document_name` matches exactly, then rebuilds the Redis BM25 corpus from Qdrant (capped like ingest).

Workspace UI preferences (per `company_id`, stored in Redis; no auth yet):
- `GET /workspace/preferences?company_id=demo`
- `PATCH /workspace/preferences?company_id=demo` with JSON body (partial fields: `theme`, `density`, `show_streaming_indicator`)

### Run the ARQ worker (separate terminal)

```bash
uv run arq backend.workers.ingestion_worker.WorkerSettings
```

### Try ingestion
- Set `OPENAI_API_KEY` in `.env` (embeddings are required for indexing).
- `POST /ingest/upload?company_id=demo` with multipart form file `file` (returns **409** if a document with the same filename already exists in that workspace)
- Poll `GET /ingest/status/{job_id}` until `ready` (response includes `chunks_indexed` when using the JSON status format)
- Ingestion timeouts: `UNSTRUCTURED_TIMEOUT_SECONDS` caps the Unstructured HTTP parse. The ARQ worker uses a **longer** default job limit (`UNSTRUCTURED_TIMEOUT_SECONDS` + `INGESTION_JOB_TIMEOUT_BUFFER_SECONDS`, or set `INGESTION_JOB_TIMEOUT_SECONDS` explicitly). The effective job limit must stay **above** the Unstructured timeout or settings validation fails at startup.

### Try streaming query
- Set `OPENAI_API_KEY` and **`COHERE_API_KEY`** in `.env` (transform, retrieval rerank, and answer generation).
- Ingest at least one document for `company_id` first so Qdrant and the Redis BM25 corpus are populated.
- `POST /query/stream` with JSON `{ "company_id": "demo", "question": "your question" }`
- SSE events: `sources` (JSON array of previews), then `token` chunks, then `done`. On failure, `error` then `done`.

### Frontend (Vite + React + Tailwind)

- Local dev **always** calls same-origin **`/api`** (ignore any `VITE_API_URL` in `frontend/.env`). Vite proxies `/api` to FastAPI; set **`VITE_DEV_API_TARGET`** (default `http://127.0.0.1:8080`) to match your `uvicorn --port`. This avoids CORS from embedded previews and mistaken `http://...` API URLs in `.env`.
- Production builds still need **`VITE_API_URL`** set for the deployed API (see `frontend/.env.example`).
- Install and run:

```bash
cd frontend
npm install
npm run dev
```

- Open the printed local URL (default port **5173**). CORS is enabled for that origin in `backend/main.py`.
- Use **Workspace** for `company_id`, **Upload** for ingestion (polls status every 2s), **Chat** for streaming queries via **`useSSE`**.
