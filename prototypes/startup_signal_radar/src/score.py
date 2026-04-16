from __future__ import annotations


def weighted_overall_score(
    *,
    pain_score: float,
    buildability_score: float,
    ai_leverage_score: float,
    distribution_fit_score: float,
    business_quality_score: float,
) -> float:
    weights = {
        "pain": 0.20,
        "buildability": 0.20,
        "ai": 0.25,
        "distribution": 0.15,
        "business": 0.20,
    }
    total = (
        pain_score * weights["pain"]
        + buildability_score * weights["buildability"]
        + ai_leverage_score * weights["ai"]
        + distribution_fit_score * weights["distribution"]
        + business_quality_score * weights["business"]
    )
    return round(total, 2)


def recommend_status(
    *,
    pain_score: float,
    buildability_score: float,
    ai_leverage_score: float,
    distribution_fit_score: float,
    business_quality_score: float,
) -> str:
    overall = weighted_overall_score(
        pain_score=pain_score,
        buildability_score=buildability_score,
        ai_leverage_score=ai_leverage_score,
        distribution_fit_score=distribution_fit_score,
        business_quality_score=business_quality_score,
    )
    if buildability_score < 5 or distribution_fit_score < 5:
        return "reject"
    if overall >= 8:
        return "prototype_next"
    if overall >= 7:
        return "research_next"
    return "watchlist"
