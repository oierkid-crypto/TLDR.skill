from __future__ import annotations

import hashlib
from collections import Counter

from models import ExtractedSignal


def cluster_identity_key(signal: ExtractedSignal) -> str:
    workflow = signal.workflow or "unknown"
    ops = "heavy_ops" if signal.heavy_ops_penalty else "software_first"
    return f"{workflow}|{ops}"


def stable_cluster_id(signals: list[ExtractedSignal]) -> str:
    if not signals:
        raise ValueError("signals must not be empty")
    keys = sorted(cluster_identity_key(signal) for signal in signals)
    digest = hashlib.sha1("||".join(keys).encode()).hexdigest()[:12]
    return f"cluster_{digest}"


def _cluster_key(signal: ExtractedSignal) -> str:
    return cluster_identity_key(signal)


def cluster_signals(signals: list[ExtractedSignal]) -> list[list[ExtractedSignal]]:
    grouped: dict[str, list[ExtractedSignal]] = {}
    for signal in signals:
        key = _cluster_key(signal)
        grouped.setdefault(key, []).append(signal)
    return list(grouped.values())


def cluster_to_problem_cluster(signals: list[ExtractedSignal], cluster_id: str | None = None) -> dict:
    if not signals:
        raise ValueError("signals must not be empty")

    workflows = [signal.workflow for signal in signals if signal.workflow]
    workflow_name = Counter(workflows).most_common(1)[0][0] if workflows else "unknown workflow"
    user_segments = [signal.user_segment for signal in signals if signal.user_segment]
    platforms = [signal.normalized_post.platform for signal in signals]
    replacement_ratio = sum(1 for signal in signals if signal.replacement_intent) / len(signals)
    seo_ratio = sum(1 for signal in signals if signal.seo_intent) / len(signals)
    cross_platform_support = len(set(platforms)) / 3
    heavy_ops = any(signal.heavy_ops_penalty for signal in signals)

    priority = "reject" if heavy_ops else ("high" if replacement_ratio >= 0.5 and len(set(platforms)) >= 2 else "medium")
    next_action = "ignore" if heavy_ops else ("prototype" if priority == "high" else "deep_research")

    evidence = []
    pain_descriptions = []
    existing_solutions = []
    failure_modes = []
    for signal in signals:
        evidence.append(
            {
                "platform": signal.normalized_post.platform,
                "url": signal.normalized_post.url,
                "excerpt": signal.evidence_excerpt,
                "user_segment_hint": signal.user_segment,
                "engagement": signal.normalized_post.engagement.model_dump(),
            }
        )
        pain_descriptions.extend(signal.pain_points)
        if signal.current_solution:
            existing_solutions.append(signal.current_solution)
        if signal.replacement_intent:
            failure_modes.append("users are actively seeking alternatives")
        if signal.heavy_ops_penalty:
            failure_modes.append("requires heavy offline/ops execution")

    unique_pains = sorted(set(pain_descriptions)) or ["workflow friction"]
    pain_points = [
        {
            "description": pain,
            "type": "manual_repetition" if pain in {"manual", "manually", "麻烦"} else "other",
            "severity": "high" if replacement_ratio >= 0.5 else "medium",
        }
        for pain in unique_pains
    ]

    final_cluster_id = cluster_id or stable_cluster_id(signals)

    return {
        "cluster_id": final_cluster_id,
        "title": signals[0].normalized_post.title or workflow_name,
        "summary": f"Users report repeated friction around {workflow_name}.",
        "primary_user_segments": sorted(set(seg for seg in user_segments if seg)) or ["general operators"],
        "workflow": {
            "name": workflow_name,
            "category": "workflow_automation",
            "repetition_level": "high" if workflow_name != "unknown workflow" else "medium",
        },
        "pain_points": pain_points,
        "existing_solutions": sorted(set(existing_solutions)),
        "failure_modes": sorted(set(failure_modes)),
        "signals": {
            "replacement_intent": round(replacement_ratio, 2),
            "willingness_to_pay_hint": 1.0 if any(signal.monetization_hint for signal in signals) else 0.0,
            "cross_platform_support": round(cross_platform_support, 2),
            "seo_intent_hint": round(seo_ratio, 2),
        },
        "evidence": evidence,
        "scores": {
            "pain_score": 7.5 if replacement_ratio >= 0.5 else 6.0,
            "buildability_score": 4.0 if heavy_ops else 8.0,
            "ai_leverage_score": 8.5 if any(signal.ai_fit for signal in signals) else 5.0,
            "distribution_fit_score": 3.5 if heavy_ops else 8.0,
            "business_quality_score": 5.0 if heavy_ops else 7.5,
            "confidence": round(min(1.0, 0.4 + 0.2 * len(signals)), 2),
        },
        "verdict": {
            "priority": priority,
            "reason": "Heavy-ops requirement lowers founder fit." if heavy_ops else "Cross-platform, replacement-seeking workflow pain matches founder filter.",
            "next_action": next_action,
        },
    }
