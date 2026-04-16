from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from reddit_source import build_reddit_collection_plan  # type: ignore  # noqa: E402
from query_builder import load_taxonomy  # type: ignore  # noqa: E402


def test_build_reddit_collection_plan_expands_seed_subreddits_and_queries() -> None:
    taxonomy = load_taxonomy("prototypes/startup_signal_radar/config/query_taxonomy.example.yaml")

    plan = build_reddit_collection_plan(
        taxonomy=taxonomy,
        market="b2b_software",
        workflows=["update CRM after calls", "meeting note cleanup"],
        user_segments=["sales teams", "founders"],
        audience_category="2b",
    )

    assert "sales" in plan["seed_subreddits"]
    assert "smallbusiness" in plan["seed_subreddits"]
    assert plan["audience_category"] == "2b"
    assert "marketers" in plan["user_segments"]
    assert len(plan["queries"]) >= 2
    assert all("line下活动" not in q for q in plan["queries"])
