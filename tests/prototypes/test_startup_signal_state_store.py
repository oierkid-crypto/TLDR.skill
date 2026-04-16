from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from state_store import load_snapshot, save_snapshot, snapshot_cluster_index  # type: ignore  # noqa: E402


def test_save_and_load_snapshot_roundtrip(tmp_path: Path) -> None:
    snapshot = {
        "report_date": "2026-04-16",
        "problem_clusters": [
            {"cluster_id": "cluster_crm", "title": "CRM update pain", "verdict": {"priority": "high"}}
        ],
    }
    target = tmp_path / "snapshot.json"

    save_snapshot(snapshot, target)
    loaded = load_snapshot(target)

    assert loaded["report_date"] == "2026-04-16"
    assert loaded["problem_clusters"][0]["cluster_id"] == "cluster_crm"


def test_snapshot_cluster_index_extracts_mentions_and_priority() -> None:
    snapshot = {
        "problem_clusters": [
            {
                "cluster_id": "cluster_crm",
                "evidence": [{"platform": "reddit"}, {"platform": "x"}],
                "verdict": {"priority": "high"},
            },
            {
                "cluster_id": "cluster_offline",
                "evidence": [{"platform": "xiaohongshu"}],
                "verdict": {"priority": "reject"},
            },
        ]
    }

    index = snapshot_cluster_index(snapshot)

    assert index["cluster_crm"]["mentions"] == 2
    assert index["cluster_crm"]["priority"] == "high"
    assert index["cluster_offline"]["mentions"] == 1
