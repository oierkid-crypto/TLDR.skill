from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from query_builder import load_taxonomy  # type: ignore  # noqa: E402
from x_source import build_x_collection_plan, build_x_search_plan, check_x_credentials  # type: ignore  # noqa: E402


TAXONOMY_PATH = "prototypes/startup_signal_radar/config/query_taxonomy.example.yaml"


def test_check_x_credentials_false_when_missing_env(monkeypatch) -> None:
    monkeypatch.delenv("X_BEARER_TOKEN", raising=False)

    assert check_x_credentials() is False


def test_build_x_search_plan_returns_query_metadata() -> None:
    plan = build_x_search_plan(query="need a better CRM tool", limit=25)

    assert plan["query"] == "need a better CRM tool"
    assert plan["limit"] == 25
    assert plan["platform"] == "x"


def test_build_x_collection_plan_supports_audience_category_and_expands_segments() -> None:
    taxonomy = load_taxonomy(TAXONOMY_PATH)

    plan = build_x_collection_plan(
        taxonomy=taxonomy,
        workflows=["update CRM after calls"],
        user_segments=["sales teams"],
        tool_or_category="CRM",
        audience_category="2b",
    )

    assert plan["audience_category"] == "2b"
    assert "marketers" in plan["user_segments"]
    assert len(plan["queries"]) >= 2
    assert all(item["platform"] == "x" for item in plan["plans"])
