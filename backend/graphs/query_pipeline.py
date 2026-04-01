"""
LangGraph query pipeline: transform, then hybrid retrieve and rerank.

Streaming generation runs outside the graph in the router.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

from backend.core.config import Settings
from backend.services.hybrid_search import retrieve_and_rerank
from backend.services.query_transformer import transform_query_for_retrieval


class QueryGraphContext(TypedDict):
    settings: Settings


class QueryState(TypedDict, total=False):
    company_id: str
    question: str
    sub_queries: list[str]
    hyde_document: str
    contexts: list[dict[str, Any]]
    error: str | None


async def _transform_node(
    state: QueryState,
    runtime: Runtime[QueryGraphContext],
) -> dict[str, Any]:
    """
    Rewrite the user question into sub-queries and a HyDE document.
    """

    if state.get("error"):
        return {}
    settings = runtime.context["settings"]
    try:
        sub_queries, hyde = await transform_query_for_retrieval(settings, state["question"])
        return {"sub_queries": sub_queries, "hyde_document": hyde}
    except Exception as exc:
        return {"error": str(exc)}


async def _retrieve_node(
    state: QueryState,
    runtime: Runtime[QueryGraphContext],
) -> dict[str, Any]:
    """
    Hybrid search plus rerank into ordered context dicts.
    """

    if state.get("error"):
        return {}
    settings = runtime.context["settings"]
    try:
        contexts = await retrieve_and_rerank(
            settings,
            state["company_id"],
            state["sub_queries"],
            state["hyde_document"],
            state["question"],
        )
        return {"contexts": contexts}
    except Exception as exc:
        return {"error": str(exc)}


_builder = StateGraph(state_schema=QueryState, context_schema=QueryGraphContext)
_builder.add_node("transform", _transform_node)
_builder.add_node("retrieve", _retrieve_node)
_builder.add_edge(START, "transform")
_builder.add_edge("transform", "retrieve")
_builder.add_edge("retrieve", END)

compiled_query_graph = _builder.compile()


async def run_query_pipeline(
    settings: Settings,
    company_id: str,
    question: str,
) -> QueryState:
    """
    Execute transform and retrieval subgraph for one question.
    """

    final: dict[str, Any] = await compiled_query_graph.ainvoke(
        {"company_id": company_id.strip(), "question": question.strip()},
        context={"settings": settings},
    )
    return final  # type: ignore[return-value]
