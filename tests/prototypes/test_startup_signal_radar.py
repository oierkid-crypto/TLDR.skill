from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from models import (  # type: ignore  # noqa: E402
    DistributionFit,
    EvidenceSummary,
    FounderFit,
    OpportunityCard,
    OpportunityDecision,
    OpportunityProblem,
    OpportunityScores,
    SolutionHypothesis,
    TargetUser,
)
from score import recommend_status, weighted_overall_score  # type: ignore  # noqa: E402


def test_weighted_overall_score_prioritizes_ai_and_distribution() -> None:
    overall = weighted_overall_score(
        pain_score=8.0,
        buildability_score=8.5,
        ai_leverage_score=9.0,
        distribution_fit_score=8.0,
        business_quality_score=7.0,
    )

    assert overall == 8.15


def test_recommend_status_rejects_heavy_ops_even_with_high_pain() -> None:
    status = recommend_status(
        pain_score=9.5,
        buildability_score=4.0,
        ai_leverage_score=7.5,
        distribution_fit_score=3.5,
        business_quality_score=6.5,
    )

    assert status == "reject"


def test_opportunity_card_captures_founder_filter_fields() -> None:
    card = OpportunityCard(
        opportunity_id="opp_001",
        title="Meeting transcript to CRM follow-up",
        problem=OpportunityProblem(
            statement="Teams still manually turn calls into CRM follow-up tasks.",
            workflow_context="Post-call sales admin",
            why_now="AI transcription is common but workflow completion remains unsolved.",
        ),
        target_user=TargetUser(
            primary_segment="small sales teams",
            search_behavior="Searches for meeting notes to CRM and follow-up automation tools.",
            pain_trigger="Every customer call generates manual cleanup work.",
            current_workarounds=["manual notes", "copy-paste into CRM"],
        ),
        ai_solution_hypothesis=SolutionHypothesis(
            product_shape="agent",
            ai_role="Extract actions, draft follow-ups, and update CRM fields.",
            mvp_scope="Turn call transcript into next actions and CRM updates.",
            key_automation_loop="Transcript in, structured CRM-ready output out.",
        ),
        founder_fit=FounderFit(
            small_team_buildable=True,
            ops_intensity="low",
            notes="Can be built as workflow SaaS by 1-2 people using existing model APIs.",
        ),
        distribution_fit=DistributionFit(
            seo_fit=True,
            self_serve_fit=True,
            distribution_notes="Intent-rich SEO around meeting-to-CRM automation.",
            suggested_entry_pages=["meeting notes to CRM", "automatic sales follow-up from transcript"],
        ),
        business_model_fit={
            "pricing_shape": "subscription per workspace",
            "repeat_usage": True,
            "standardizable": True,
            "expansion_paths": ["email drafting", "account summaries"],
        },
        evidence_summary=EvidenceSummary(
            platforms=["reddit", "x"],
            representative_quotes=[
                "I still spend too much time cleaning up AI meeting notes.",
                "Need a tool that updates CRM after calls automatically.",
            ],
            signal_summary="Repeated complaint around transcription without execution.",
        ),
        scores=OpportunityScores(
            pain_score=8.5,
            buildability_score=8.0,
            ai_leverage_score=9.0,
            distribution_fit_score=8.5,
            business_quality_score=7.5,
            overall_score=8.35,
        ),
        decision=OpportunityDecision(
            status="prototype_next",
            reason="High-frequency problem with strong AI leverage and self-serve acquisition potential.",
            immediate_next_step="Prototype transcript-to-CRM action extraction flow.",
        ),
    )

    assert card.founder_fit.small_team_buildable is True
    assert card.distribution_fit.seo_fit is True
    assert card.decision.status == "prototype_next"
