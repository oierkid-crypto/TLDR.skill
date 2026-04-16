from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from reports import build_opportunity_queue, build_weekly_summary  # type: ignore  # noqa: E402


SAMPLE_OPPORTUNITIES = [
    {
        "title": "Meeting transcript to CRM follow-up",
        "scores": {"overall_score": 8.6},
        "decision": {"status": "prototype_next"},
        "founder_fit": {"ops_intensity": "low", "small_team_buildable": True},
        "distribution_fit": {"seo_fit": True},
        "evidence_summary": {"platforms": ["reddit", "x"], "signal_summary": "Repeated replacement intent."},
    },
    {
        "title": "Offline parent community coordination",
        "scores": {"overall_score": 4.8},
        "decision": {"status": "reject"},
        "founder_fit": {"ops_intensity": "high", "small_team_buildable": False},
        "distribution_fit": {"seo_fit": False},
        "evidence_summary": {"platforms": ["xiaohongshu"], "signal_summary": "Heavy offline ops burden."},
    },
]


def test_build_opportunity_queue_surfaces_founder_relevant_columns() -> None:
    queue = build_opportunity_queue(SAMPLE_OPPORTUNITIES)

    assert queue[0]["title"] == "Meeting transcript to CRM follow-up"
    assert queue[0]["decision"] == "prototype_next"
    assert queue[0]["seo_fit"] is True
    assert queue[1]["ops_intensity"] == "high"


def test_build_weekly_summary_counts_priority_buckets() -> None:
    summary = build_weekly_summary(SAMPLE_OPPORTUNITIES, week_label="2026-W16")

    assert summary["week_label"] == "2026-W16"
    assert summary["summary"]["prototype_next"] == 1
    assert summary["summary"]["rejected"] == 1
    assert summary["top_queue"][0]["title"] == "Meeting transcript to CRM follow-up"
