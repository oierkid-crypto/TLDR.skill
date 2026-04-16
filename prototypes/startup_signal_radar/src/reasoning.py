from __future__ import annotations


def explain_opportunity_decision(opportunity: dict) -> str:
    status = opportunity["decision"]["status"]
    scores = opportunity["scores"]
    founder_fit = opportunity["founder_fit"]
    seo_fit = opportunity["distribution_fit"]["seo_fit"]
    signal_summary = opportunity["evidence_summary"].get("signal_summary", "")

    if status == "reject":
        return (
            f"该方向当前不适合：虽然有一定痛点，但更偏重运营/重协调，"
            f"对1-2人团队不友好；AI杠杆和SEO获客都不足。"
            f"补充信号：{signal_summary}"
        )

    return (
        f"该方向值得继续推进：痛点分{scores['pain_score']:.1f}，可做性{scores['buildability_score']:.1f}，"
        f"AI杠杆{scores['ai_leverage_score']:.1f}。"
        f"它更适合1-2人团队，运营强度为{founder_fit['ops_intensity']}，"
        f"{'具备' if seo_fit else '暂不具备'}SEO/自助获客潜力。"
        f"补充信号：{signal_summary}"
    )
