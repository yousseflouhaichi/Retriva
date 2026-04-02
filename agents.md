# Multimodal RAG Platform

## What this is
A production-grade multimodal RAG SaaS platform. Companies upload documents
(PDFs, DOCX, images) and query them via a chat interface. Each company's data
is fully isolated via `company_id` / workspace namespacing in Qdrant.

## Stack
- Backend: FastAPI (async route handlers), Python 3.13, uv for packages
- Task queue: ARQ + Redis, not FastAPI BackgroundTasks for ingestion
- Vector DB: Qdrant namespaced per workspace / tenant
- Retrieval: Hybrid search (dense + BM25) + RRF + Cohere reranking (see `retrieval` rules and config)
- Query transformation: Multi-query rewriting + HyDE before retrieval (see query pipeline)
- Embeddings: OpenAI `text-embedding-3-large`, 3072 dimensions (configurable via settings)
- Parsing: Unstructured.io via Docker
- **Multimodal**: image captioning / vision at ingestion is a **product target**; implement and document when added to the pipeline
- Orchestration: LangGraph (or `backend/graphs`) for the query pipeline
- Streaming: SSE (e.g. sse-starlette), no full-response buffering for chat
- Frontend: React + Vite + Tailwind + shadcn-style UI components

## Non-negotiables
- Never use FastAPI BackgroundTasks for ingestion; use ARQ
- Never query across tenant collections in Qdrant
- Never skip query transformation before retrieval
- Never buffer the full LLM answer for streaming endpoints; stream via SSE
- Never use pip; use uv
- Pydantic v2 only in Python
- All runtime configuration through `core/config.py` / `get_settings()`, not scattered `os.environ` reads
- **FastAPI route handlers** must be `async`; small pure helpers may be sync when they do not block the event loop

## Type hints
Required on public Python APIs and non-trivial functions; use precise types in core logic. Prefer narrow types over `Any` except at clear boundaries (e.g. raw JSON).
