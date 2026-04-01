"""
Reciprocal Rank Fusion for merging ordered candidate id lists.
"""

from __future__ import annotations


def reciprocal_rank_fusion(rankings: list[list[str]], k: int) -> list[tuple[str, float]]:
    """
    Fuse multiple ranked id lists with RRF.

    Args:
        rankings: Each inner list is best-first point ids (dense or lexical runs).
        k: RRF constant from configuration (typically 60).

    Returns:
        list[tuple[str, float]]: Ids sorted by fused score descending.
    """

    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, point_id in enumerate(ranking):
            if not point_id:
                continue
            scores[point_id] = scores.get(point_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda item: -item[1])
