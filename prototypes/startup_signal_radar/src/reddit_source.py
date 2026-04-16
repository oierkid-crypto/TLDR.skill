from __future__ import annotations

import os
from urllib.parse import quote_plus

from query_builder import audience_seed_segments, build_queries


REDDIT_SEED_SUBREDDITS = {
    "b2b_software": ["sales", "smallbusiness", "Entrepreneur", "SaaS", "startups"],
    "developer_tools": ["webdev", "devops", "programming", "selfhosted"],
    "2b": ["sales", "smallbusiness", "Entrepreneur", "SaaS", "startups"],
    "2c": ["Frugal", "buyitforlife", "productivity", "skincareaddiction", "personalfinance"],
    "2p": ["creators", "freelance", "Entrepreneur", "selfhosted", "webdev"],
}


def check_reddit_credentials() -> bool:
    required = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT"]
    return all(bool(os.getenv(key)) for key in required)


def build_reddit_plan(*, subreddits: list[str], query: str, limit: int = 100) -> dict:
    joined = "+".join(subreddits)
    return {
        "subreddits": subreddits,
        "query": query,
        "limit": limit,
        "search_path": f"https://www.reddit.com/r/{joined}/search?q={quote_plus(query)}&restrict_sr=on&sort=new",
        "credential_ready": check_reddit_credentials(),
    }


def build_reddit_request_headers(*, user_agent: str) -> dict:
    return {"User-Agent": user_agent}


def preview_reddit_fetch_job(*, subreddits: list[str], query: str, user_agent: str, limit: int = 100) -> dict:
    plan = build_reddit_plan(subreddits=subreddits, query=query, limit=limit)
    plan["headers"] = build_reddit_request_headers(user_agent=user_agent)
    return plan


def build_reddit_collection_plan(
    *,
    taxonomy: dict,
    market: str,
    workflows: list[str],
    user_segments: list[str],
    tool_or_category: str = "CRM",
    audience_category: str | None = None,
) -> dict:
    category_subreddits = REDDIT_SEED_SUBREDDITS.get(audience_category or "", [])
    seed_subreddits = REDDIT_SEED_SUBREDDITS.get(market, ["Entrepreneur", "smallbusiness"])
    if category_subreddits:
        seed_subreddits = list(dict.fromkeys(category_subreddits + seed_subreddits))

    effective_user_segments = list(dict.fromkeys(user_segments + audience_seed_segments(taxonomy, audience_category)))
    queries: list[str] = []
    for workflow in workflows:
        for user_segment in effective_user_segments:
            queries.extend(
                build_queries(
                    taxonomy,
                    platform="reddit",
                    tool_or_category=tool_or_category,
                    workflow=workflow,
                    user_segment=user_segment,
                    audience_category=audience_category,
                )
            )
    deduped_queries = list(dict.fromkeys(queries))
    plans = [build_reddit_plan(subreddits=seed_subreddits, query=query, limit=100) for query in deduped_queries]
    return {
        "market": market,
        "audience_category": audience_category,
        "seed_subreddits": seed_subreddits,
        "user_segments": effective_user_segments,
        "queries": deduped_queries,
        "plans": plans,
    }
