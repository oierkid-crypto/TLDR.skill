from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from query_builder import audience_seed_segments, build_queries, load_taxonomy  # type: ignore  # noqa: E402


def test_load_taxonomy_reads_positive_and_downrank_groups() -> None:
    taxonomy = load_taxonomy("prototypes/startup_signal_radar/config/query_taxonomy.example.yaml")

    assert "pain_words" in taxonomy["positive_signal_groups"]
    assert "heavy_ops_markers" in taxonomy["downrank_signal_groups"]
    assert "2b" in taxonomy["audience_categories"]
    assert "2p" in taxonomy["audience_categories"]


def test_audience_seed_segments_returns_category_specific_user_segments() -> None:
    taxonomy = load_taxonomy("prototypes/startup_signal_radar/config/query_taxonomy.example.yaml")

    segments = audience_seed_segments(taxonomy, "2p")

    assert "creators" in segments
    assert "developers" in segments


def test_build_queries_generates_founder_filter_aware_templates() -> None:
    taxonomy = load_taxonomy("prototypes/startup_signal_radar/config/query_taxonomy.example.yaml")

    queries = build_queries(
        taxonomy,
        platform="reddit",
        tool_or_category="CRM",
        workflow="update CRM after calls",
        user_segment="sales teams",
        audience_category="2b",
    )

    assert any("alternative to" in query.lower() for query in queries)
    assert any("sales teams" in query for query in queries)
    assert any("2b CRM update CRM after calls" in query for query in queries)
    assert all("线下活动" not in query for query in queries)
