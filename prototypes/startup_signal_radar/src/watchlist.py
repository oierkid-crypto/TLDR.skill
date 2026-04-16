from __future__ import annotations


def build_watchlist(problem_clusters: list[dict]) -> list[dict]:
    kept = [cluster for cluster in problem_clusters if cluster["verdict"]["priority"] != "reject"]
    return sorted(kept, key=lambda item: item["scores"]["buildability_score"] + item["scores"]["distribution_fit_score"], reverse=True)


def summarize_trends(previous: dict, current: dict) -> dict:
    rising = []
    stable_or_down = []
    for cluster_id, current_state in current.items():
        previous_state = previous.get(cluster_id, {"mentions": 0, "priority": "unknown"})
        delta = current_state["mentions"] - previous_state["mentions"]
        record = {
            "cluster_id": cluster_id,
            "mentions_delta": delta,
            "previous_priority": previous_state["priority"],
            "current_priority": current_state["priority"],
        }
        if delta > 0:
            rising.append(record)
        else:
            stable_or_down.append(record)

    rising.sort(key=lambda item: item["mentions_delta"], reverse=True)
    stable_or_down.sort(key=lambda item: item["mentions_delta"])
    return {"rising": rising, "stable_or_down": stable_or_down}
