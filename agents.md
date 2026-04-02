# Multimodal RAG Platform

## What this is
A multimodal RAG-style application: workspaces upload documents, chunks are embedded and stored per tenant, and users query via chat with retrieval and generation. Data is isolated by `company_id` / workspace id in Qdrant and related Redis keys (BM25, workspace preferences).

## Stack (as implemented)
- **Backend:** FastAPI, async route handlers, Python 3.13, **uv** for dependencies
- **Queue:** **ARQ** + Redis for ingestion (not FastAPI `BackgroundTasks`)
- **Vectors:** Qdrant, one collection per normalized workspace id
- **Lexical:** BM25 in Redis, keyed per tenant
- **Parsing:** Unstructured.io over HTTP, typically via Docker Compose
- **Chunking / embedding:** `backend/services/chunker.py` and `embedder.py`, tuned via `core/config.py`
- **Query path:** graph under `backend/graphs/` (e.g. `query_pipeline.py`): transform, hybrid retrieval, rerank, generate; **SSE** via `sse-starlette` (`EventSourceResponse` on `/query/stream`)
- **Frontend:** React, Vite, Tailwind, shadcn-style UI components

## Product targets (add when implemented; keep this file in sync)
- **Vision / captioning at ingest** for images inside documents
- **Richer chunk payloads** (e.g. image paths, section headers) when retrieval and UI need them
- **Finer ingest progress** (phase or percent) while keeping Redis job keys as the source of status

## Non-negotiables
- **Ingestion** runs in the **ARQ worker** after enqueue, not inside the upload request lifecycle
- **No cross-tenant reads** in Qdrant; do not mix BM25 or prefs keys across workspaces
- **Query transformation** before retrieval; do not use only the raw user string as the retrieval input to Qdrant
- **Streaming** for chat: do not buffer the full model reply before sending events to the client
- **uv**, not pip, for Python packages
- **Pydantic v2** for API models
- **Configuration** via `core/config.py` / `get_settings()`; do not read `os.environ` outside config
- **FastAPI route handlers** are `async`; offload blocking work with `asyncio.to_thread` or keep it in the worker

## Engineering defaults
- **Routers** stay thin; **services** hold business logic; **workers** own long-running jobs
- **Types:** prefer precise Python types in core logic; use `Any` sparingly at boundaries (e.g. raw JSON)
- **Errors:** map to safe HTTP `detail` for clients; log with context, never secrets
- **Tests** on critical paths (ingest, workspaces, documents, query) when behavior changes

## Type hints
Use type hints on public Python APIs and non-trivial functions. Prefer narrow types over `Any` except at clear boundaries (e.g. parsed JSON).
