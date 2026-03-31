# Multimodal RAG Platform

## What this is
A production-grade multimodal RAG SaaS platform. Companies upload documents
(PDFs, DOCX, images) and query them via a chat interface. Each company's data
is fully isolated via company_id namespacing in Qdrant.

## Stack
- Backend: FastAPI async, Python 3.13, uv for packages
- Task queue: ARQ + Redis, never FastAPI BackgroundTasks for ingestion
- Vector DB: Qdrant namespaced by company_id
- Retrieval: Hybrid search (dense + BM25) + RRF + Cohere reranking
- Query transformation: Multi-query rewriting + HyDE before every retrieval
- Embeddings: OpenAI text-embedding-3-large, 3072 dimensions
- Parsing: Unstructured.io self-hosted via Docker
- Image captioning: GPT-4o vision at ingestion time
- Orchestration: LangGraph for the query pipeline
- Streaming: SSE via sse-starlette
- Frontend: React + Vite + Tailwind CSS + shadcn/ui

## Non-negotiables
- Never use FastAPI BackgroundTasks for ingestion, use ARQ
- Never query across company collections in Qdrant
- Never skip query transformation before retrieval
- Never buffer LLM responses, always stream via SSE
- Never use pip, always uv
- Pydantic v2 syntax only, never v1 patterns
- All config from core/config.py, never hardcode values or read os.environ directly
- All functions must be async in FastAPI
- Type hints required on every function signature