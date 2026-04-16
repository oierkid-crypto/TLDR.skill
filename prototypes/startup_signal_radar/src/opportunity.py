from __future__ import annotations

from models import (
    BusinessModelFit,
    DistributionFit,
    EvidenceSummary,
    ExtractedSignal,
    FounderFit,
    OpportunityCard,
    OpportunityDecision,
    OpportunityProblem,
    OpportunityScores,
    SolutionHypothesis,
    TargetUser,
)
from reasoning import explain_opportunity_decision
from score import weighted_overall_score, recommend_status


def _pain_score(signal: ExtractedSignal) -> float:
    base = 5.0 + min(len(signal.pain_points), 3)
    if signal.replacement_intent:
        base += 1.0
    if signal.seo_intent:
        base += 0.5
    if signal.workflow:
        base += 0.5
    return min(base, 10.0)


def _buildability_score(signal: ExtractedSignal) -> float:
    score = 8.0 if signal.ai_fit else 6.0
    if signal.heavy_ops_penalty:
        score -= 4.0
    return max(min(score, 10.0), 0.0)


def _distribution_fit_score(signal: ExtractedSignal) -> float:
    score = 8.0 if signal.seo_intent else 5.5
    if signal.heavy_ops_penalty:
        score -= 3.5
    return max(min(score, 10.0), 0.0)


def score_opportunity(signal: ExtractedSignal) -> dict:
    pain_score = _pain_score(signal)
    buildability_score = _buildability_score(signal)
    ai_leverage_score = 9.0 if signal.ai_fit and signal.replacement_intent else (8.5 if signal.ai_fit else 4.5)
    distribution_fit_score = _distribution_fit_score(signal)
    business_quality_score = 8.0 if signal.workflow and not signal.heavy_ops_penalty and signal.seo_intent else (7.5 if signal.workflow and not signal.heavy_ops_penalty else 5.0)
    overall = weighted_overall_score(
        pain_score=pain_score,
        buildability_score=buildability_score,
        ai_leverage_score=ai_leverage_score,
        distribution_fit_score=distribution_fit_score,
        business_quality_score=business_quality_score,
    )
    status = recommend_status(
        pain_score=pain_score,
        buildability_score=buildability_score,
        ai_leverage_score=ai_leverage_score,
        distribution_fit_score=distribution_fit_score,
        business_quality_score=business_quality_score,
    )

    card = OpportunityCard(
        opportunity_id=f"opp_{signal.normalized_post.post_id}",
        title=signal.normalized_post.title or signal.normalized_post.raw_text.splitlines()[0],
        problem=OpportunityProblem(
            statement=signal.normalized_post.raw_text.splitlines()[0],
            workflow_context=signal.workflow or "unknown workflow",
            why_now="Users are openly expressing repeated friction and unmet need online.",
        ),
        target_user=TargetUser(
            primary_segment=signal.user_segment or "general operators",
            search_behavior="Searches for alternatives and automation workflows online." if signal.seo_intent else "Unclear search behavior.",
            pain_trigger=signal.evidence_excerpt,
            current_workarounds=[signal.current_solution] if signal.current_solution else [],
        ),
        ai_solution_hypothesis=SolutionHypothesis(
            product_shape="agent" if signal.ai_fit else "workflow_tool",
            ai_role="Automate extraction, summarization, and workflow completion." if signal.ai_fit else "Limited AI leverage.",
            mvp_scope=signal.workflow or "narrow workflow automation",
            key_automation_loop=f"Input user content, output {signal.workflow or 'structured workflow result'}.",
        ),
        founder_fit=FounderFit(
            small_team_buildable=buildability_score >= 5,
            ops_intensity="high" if signal.heavy_ops_penalty else "low",
            notes="Downranked for heavy offline/service burden." if signal.heavy_ops_penalty else "Fits a small-team AI software build.",
        ),
        distribution_fit=DistributionFit(
            seo_fit=signal.seo_intent,
            self_serve_fit=not signal.heavy_ops_penalty,
            distribution_notes="Search-intent rich opportunity." if signal.seo_intent else "Would need stronger distribution proof.",
            suggested_entry_pages=[signal.workflow] if signal.workflow else [],
        ),
        business_model_fit=BusinessModelFit(
            pricing_shape="subscription" if not signal.heavy_ops_penalty else "service-heavy",
            repeat_usage=bool(signal.workflow),
            standardizable=not signal.heavy_ops_penalty,
            expansion_paths=["templates", "automation"] if signal.ai_fit else [],
        ),
        evidence_summary=EvidenceSummary(
            platforms=[signal.normalized_post.platform],
            representative_quotes=[signal.evidence_excerpt],
            signal_summary="Replacement/search intent present." if signal.replacement_intent else "Complaint detected.",
        ),
        scores=OpportunityScores(
            pain_score=pain_score,
            buildability_score=buildability_score,
            ai_leverage_score=ai_leverage_score,
            distribution_fit_score=distribution_fit_score,
            business_quality_score=business_quality_score,
            overall_score=overall,
        ),
        decision=OpportunityDecision(
            status=status,
            reason="Rejected for low buildability/distribution." if status == "reject" else "Promising under founder filter.",
            immediate_next_step="prototype workflow" if status == "prototype_next" else "refine positioning",
        ),
    )
    dumped = card.model_dump()
    dumped["founder_reasoning"] = explain_opportunity_decision(dumped)
    return dumped
