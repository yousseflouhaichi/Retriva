"""
Hybrid retrieval: BM25 over Redis corpus, multi dense Qdrant searches, RRF, Cohere rerank.
"""

from __future__ import annotations

from typing import Any

import cohere
from qdrant_client import AsyncQdrantClient
from rank_bm25 import BM25Okapi

from backend.core.config import Settings
from backend.services.bm25_index import load_bm25_corpus
from backend.services.collections import company_collection_name, company_safe_id
from backend.services.embedder import embed_texts
from backend.services.rrf import reciprocal_rank_fusion


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


async def retrieve_and_rerank(
    settings: Settings,
    company_id: str,
    sub_queries: list[str],
    hyde_document: str,
    original_question: str,
) -> list[dict[str, Any]]:
    """
    Run BM25 and dense searches, fuse with RRF, then Cohere rerank for final contexts.

    Args:
        settings: Limits, models, and service URLs.
        company_id: Tenant id (same as ingestion).
        sub_queries: Rewritten queries from the transformer.
        hyde_document: Hypothetical passage for an extra dense vector.
        original_question: User text for BM25 and rerank query.

    Returns:
        list[dict[str, Any]]: Ordered context dicts with text and citation fields.

    Raises:
        ValueError: When Cohere API key is missing.
    """

    if not settings.cohere_api_key.strip():
        raise ValueError("COHERE_API_KEY is required for reranking")

    collection = company_collection_name(company_id)
    safe = company_safe_id(company_id)

    bm25_ids: list[str] = []
    corpus_ids, corpus_texts = await load_bm25_corpus(settings, safe)
    if corpus_texts:
        tokenized_corpus = [_tokenize(t) for t in corpus_texts]
        bm25 = BM25Okapi(tokenized_corpus)
        combined_q = f"{original_question.strip()} {' '.join(sub_queries)}".strip()
        query_tokens = _tokenize(combined_q)
        if not query_tokens:
            query_tokens = ["query"]
        scores = bm25.get_scores(query_tokens)
        ranked_indices = sorted(range(len(scores)), key=lambda idx: scores[idx], reverse=True)
        top_n = min(settings.bm25_top_k, len(ranked_indices))
        bm25_ids = [corpus_ids[ranked_indices[i]] for i in range(top_n)]

    texts_for_embedding = list(sub_queries) + [hyde_document]
    vectors = await embed_texts(settings, texts_for_embedding)

    ranked_lists: list[list[str]] = [bm25_ids]
    qdrant = AsyncQdrantClient(url=settings.qdrant_url)
    try:
        if not await qdrant.collection_exists(collection_name=collection):
            return []

        for vector in vectors:
            response = await qdrant.query_points(
                collection_name=collection,
                query=vector,
                limit=settings.dense_top_k_per_subquery,
                with_payload=True,
            )
            ranked_lists.append([str(hit.id) for hit in response.points])

        fused = reciprocal_rank_fusion(ranked_lists, settings.rrf_k)
        pool = min(settings.rerank_candidate_pool, len(fused))
        candidate_ids = [point_id for point_id, _score in fused[:pool]]
        if not candidate_ids:
            return []

        id_to_payload: dict[str, dict[str, Any]] = {}
        batch_size = 64
        for start in range(0, len(candidate_ids), batch_size):
            batch_ids = candidate_ids[start : start + batch_size]
            records = await qdrant.retrieve(
                collection_name=collection,
                ids=batch_ids,
                with_payload=True,
            )
            for record in records:
                payload = record.payload or {}
                id_to_payload[str(record.id)] = dict(payload)

        ordered_texts: list[str] = []
        ordered_meta: list[dict[str, Any]] = []
        for point_id in candidate_ids:
            payload = id_to_payload.get(point_id)
            if not payload:
                continue
            text = str(payload.get("text", ""))
            if not text:
                continue
            ordered_texts.append(text)
            ordered_meta.append(
                {
                    "point_id": point_id,
                    "text": text,
                    "document_name": str(payload.get("document_name", "")),
                    "page_number": int(payload.get("page_number", 0) or 0),
                }
            )

        if not ordered_texts:
            return []

        co_client = cohere.AsyncClient(api_key=settings.cohere_api_key)
        rerank_response = await co_client.rerank(
            model=settings.cohere_rerank_model,
            query=original_question.strip(),
            documents=ordered_texts,
            top_n=min(settings.rerank_top_n, len(ordered_texts)),
        )

        results: list[dict[str, Any]] = []
        for item in rerank_response.results:
            idx = item.index
            if 0 <= idx < len(ordered_meta):
                row = dict(ordered_meta[idx])
                row["rerank_score"] = float(item.relevance_score)
                results.append(row)
        return results
    finally:
        await qdrant.close()
