from __future__ import annotations

import json
from pathlib import Path


def save_snapshot(snapshot: dict, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2))


def load_snapshot(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


def snapshot_cluster_index(snapshot: dict) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for cluster in snapshot.get("problem_clusters", []):
        cluster_id = cluster["cluster_id"]
        result[cluster_id] = {
            "mentions": len(cluster.get("evidence", [])),
            "priority": cluster.get("verdict", {}).get("priority", "unknown"),
        }
    return result
