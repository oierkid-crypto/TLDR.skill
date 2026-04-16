from __future__ import annotations


def build_opportunity_queue(opportunities: list[dict]) -> list[dict]:
    ranked = sorted(
        opportunities,
        key=lambda item: item["scores"]["overall_score"],
        reverse=True,
    )
    queue = []
    for item in ranked:
        queue.append(
            {
                "title": item["title"],
                "overall_score": item["scores"]["overall_score"],
                "decision": item["decision"]["status"],
                "ops_intensity": item["founder_fit"]["ops_intensity"],
                "small_team_buildable": item["founder_fit"]["small_team_buildable"],
                "seo_fit": item["distribution_fit"]["seo_fit"],
                "platforms": item["evidence_summary"]["platforms"],
                "signal_summary": item["evidence_summary"]["signal_summary"],
                "founder_reasoning": item.get("founder_reasoning", ""),
            }
        )
    return queue


def build_daily_report(opportunities: list[dict], report_date: str) -> dict:
    ranked = sorted(
        opportunities,
        key=lambda item: item["scores"]["overall_score"],
        reverse=True,
    )
    return {
        "report_date": report_date,
        "summary": {
            "opportunities_evaluated": len(opportunities),
            "prototype_next": sum(1 for item in opportunities if item["decision"]["status"] == "prototype_next"),
            "rejected": sum(1 for item in opportunities if item["decision"]["status"] == "reject"),
        },
        "top_opportunities": ranked,
        "opportunity_queue": build_opportunity_queue(opportunities),
    }


def build_weekly_summary(opportunities: list[dict], week_label: str) -> dict:
    queue = build_opportunity_queue(opportunities)
    return {
        "week_label": week_label,
        "summary": {
            "opportunities_evaluated": len(opportunities),
            "prototype_next": sum(1 for item in opportunities if item["decision"]["status"] == "prototype_next"),
            "research_next": sum(1 for item in opportunities if item["decision"]["status"] == "research_next"),
            "watchlist": sum(1 for item in opportunities if item["decision"]["status"] == "watchlist"),
            "rejected": sum(1 for item in opportunities if item["decision"]["status"] == "reject"),
        },
        "top_queue": queue,
    }
