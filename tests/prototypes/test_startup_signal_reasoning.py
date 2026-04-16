from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from reasoning import explain_opportunity_decision  # type: ignore  # noqa: E402


def test_explain_opportunity_decision_highlights_founder_fit() -> None:
    explanation = explain_opportunity_decision(
        {
            "title": "Meeting transcript to CRM follow-up",
            "scores": {
                "pain_score": 8.5,
                "buildability_score": 8.0,
                "ai_leverage_score": 9.0,
                "distribution_fit_score": 8.5,
                "business_quality_score": 7.5,
                "overall_score": 8.4,
            },
            "decision": {"status": "prototype_next"},
            "founder_fit": {"ops_intensity": "low", "small_team_buildable": True},
            "distribution_fit": {"seo_fit": True},
            "evidence_summary": {"signal_summary": "Users actively seek alternatives."},
        }
    )

    assert "1-2人" in explanation
    assert "SEO" in explanation
    assert "AI" in explanation


def test_explain_opportunity_decision_rejects_heavy_ops_in_plain_language() -> None:
    explanation = explain_opportunity_decision(
        {
            "title": "Offline parent community coordination",
            "scores": {
                "pain_score": 7.0,
                "buildability_score": 3.5,
                "ai_leverage_score": 4.0,
                "distribution_fit_score": 3.0,
                "business_quality_score": 4.5,
                "overall_score": 4.3,
            },
            "decision": {"status": "reject"},
            "founder_fit": {"ops_intensity": "high", "small_team_buildable": False},
            "distribution_fit": {"seo_fit": False},
            "evidence_summary": {"signal_summary": "Heavily offline and coordination-driven."},
        }
    )

    assert "重运营" in explanation
    assert "不适合" in explanation
