from __future__ import annotations

import os

from query_builder import audience_seed_segments, build_queries


def check_x_credentials() -> bool:
    return bool(os.getenv("X_BEARER_TOKEN"))


def build_x_search_plan(*, query: str, limit: int = 100) -> dict:
    return {
        "platform": "x",
        "query": query,
        "limit": limit,
        "credential_ready": check_x_credentials(),
    }


def build_x_collection_plan(
    *,
    taxonomy: dict,
    workflows: list[str],
    user_segments: list[str],
    tool_or_category: str = "CRM",
    audience_category: str | None = None,
) -> dict:
    effective_user_segments = list(dict.fromkeys(user_segments + audience_seed_segments(taxonomy, audience_category)))
    queries: list[str] = []
    for workflow in workflows:
        for user_segment in effective_user_segments:
            queries.extend(
                build_queries(
                    taxonomy,
                    platform="x",
                    tool_or_category=tool_or_category,
                    workflow=workflow,
                    user_segment=user_segment,
                    audience_category=audience_category,
                )
            )
    deduped_queries = list(dict.fromkeys(queries))
    plans = [build_x_search_plan(query=query, limit=100) for query in deduped_queries]
    return {
        "audience_category": audience_category,
        "user_segments": effective_user_segments,
        "queries": deduped_queries,
        "plans": plans,
    }
