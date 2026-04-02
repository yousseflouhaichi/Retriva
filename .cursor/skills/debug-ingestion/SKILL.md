# Skill: Debug the ingestion pipeline

Use this when ingestion jobs are failing, stuck, or producing bad chunks.

## Checklist
1. Check all Docker services are healthy:
   docker compose ps
2. Check ARQ worker is running and connected to Redis
3. Check job status via GET /ingest/status/{job_id}
4. Check Unstructured is reachable:
   curl http://localhost:8000/healthcheck
5. Check Qdrant is reachable:
   curl http://localhost:6333/health
6. Check the uploads/ directory has the file saved correctly
7. Check the Qdrant collection exists for the company_id
8. Check chunk payloads have all required fields:
   workspace_id, document_name, page_number, chunk_type, parent_chunk_id

## Common failures
- Job stuck at processing: ARQ worker crashed, restart it
- Empty chunks: Unstructured failed to parse, check Unstructured logs
- No images captioned: GPT-4o call failed, check OPENAI_API_KEY in .env
- Qdrant insert failed: collection does not exist, check ensure_collection_exists was called
- BM25 index missing: company_id mismatch between ingestion and retrieval