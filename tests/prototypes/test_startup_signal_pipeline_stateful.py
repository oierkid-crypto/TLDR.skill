from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from pipeline import run_and_persist_fixture_pipeline, run_fixture_pipeline  # type: ignore  # noqa: E402
from state_store import load_snapshot, save_snapshot  # type: ignore  # noqa: E402


def test_run_fixture_pipeline_uses_previous_snapshot_for_trend_summary(tmp_path: Path) -> None:
    previous = {
        "report_date": "2026-04-15",
        "problem_clusters": [
            {
                "cluster_id": "cluster_1",
                "evidence": [{"platform": "reddit"}],
                "verdict": {"priority": "medium"},
            }
        ],
    }
    prev_path = tmp_path / "prev.json"
    save_snapshot(previous, prev_path)

    report = run_fixture_pipeline(
        platforms=["reddit", "x", "xiaohongshu"],
        report_date="2026-04-16",
        previous_snapshot_path=prev_path,
    )

    assert "trend_summary" in report
    assert report["trend_summary"]["rising"]
    assert report["watchlist"]


def test_run_and_persist_fixture_pipeline_writes_report_and_snapshot(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    state_dir = tmp_path / "state"

    result = run_and_persist_fixture_pipeline(
        platforms=["reddit", "x", "xiaohongshu"],
        report_date="2026-04-16",
        output_dir=output_dir,
        state_dir=state_dir,
    )

    report_path = Path(result["report_path"])
    snapshot_path = Path(result["snapshot_path"])

    assert report_path.exists()
    assert snapshot_path.exists()
    assert result["previous_snapshot_path"] is None

    saved_report = load_snapshot(report_path)
    saved_snapshot = load_snapshot(snapshot_path)
    assert saved_report["report_date"] == "2026-04-16"
    assert saved_snapshot["problem_clusters"]
    assert saved_snapshot["watchlist"] == saved_report["watchlist"]


def test_run_and_persist_fixture_pipeline_auto_discovers_previous_snapshot(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    state_dir = tmp_path / "state"
    previous = {
        "report_date": "2026-04-15",
        "problem_clusters": [
            {
                "cluster_id": "cluster_1",
                "evidence": [{"platform": "reddit"}],
                "verdict": {"priority": "medium"},
            }
        ],
    }
    prev_path = state_dir / "fixture_snapshot.2026-04-15.json"
    save_snapshot(previous, prev_path)

    result = run_and_persist_fixture_pipeline(
        platforms=["reddit", "x", "xiaohongshu"],
        report_date="2026-04-16",
        output_dir=output_dir,
        state_dir=state_dir,
    )

    assert result["previous_snapshot_path"] == str(prev_path)
    assert result["report"]["trend_summary"]["rising"]
