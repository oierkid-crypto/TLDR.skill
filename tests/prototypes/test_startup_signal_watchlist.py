from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from watchlist import build_watchlist, summarize_trends  # type: ignore  # noqa: E402


CLUSTERS = [
    {
        "cluster_id": "cluster_crm",
        "title": "CRM update automation pain",
        "signals": {"replacement_intent": 1.0, "cross_platform_support": 0.67},
        "scores": {"pain_score": 7.5, "buildability_score": 8.0, "ai_leverage_score": 8.5, "distribution_fit_score": 8.0, "business_quality_score": 7.5},
        "verdict": {"priority": "high", "next_action": "prototype"},
    },
    {
        "cluster_id": "cluster_offline",
        "title": "Offline community operations burden",
        "signals": {"replacement_intent": 0.2, "cross_platform_support": 0.33},
        "scores": {"pain_score": 6.0, "buildability_score": 4.0, "ai_leverage_score": 4.5, "distribution_fit_score": 3.0, "business_quality_score": 5.0},
        "verdict": {"priority": "reject", "next_action": "ignore"},
    },
]

PREVIOUS = {
    "cluster_crm": {"mentions": 3, "priority": "medium"},
    "cluster_offline": {"mentions": 2, "priority": "reject"},
}

CURRENT = {
    "cluster_crm": {"mentions": 6, "priority": "high"},
    "cluster_offline": {"mentions": 1, "priority": "reject"},
}


def test_build_watchlist_keeps_only_non_rejected_clusters() -> None:
    watchlist = build_watchlist(CLUSTERS)

    assert len(watchlist) == 1
    assert watchlist[0]["cluster_id"] == "cluster_crm"


def test_summarize_trends_identifies_rising_clusters() -> None:
    summary = summarize_trends(PREVIOUS, CURRENT)

    assert summary["rising"][0]["cluster_id"] == "cluster_crm"
    assert summary["stable_or_down"][0]["cluster_id"] == "cluster_offline"
