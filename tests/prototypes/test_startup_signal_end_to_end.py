from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from pipeline import run_fixture_pipeline  # type: ignore  # noqa: E402


def test_run_fixture_pipeline_builds_founder_facing_report() -> None:
    report = run_fixture_pipeline(platforms=["reddit", "x", "xiaohongshu"], report_date="2026-04-16")

    assert report["report_date"] == "2026-04-16"
    assert report["summary"]["opportunities_evaluated"] >= 1
    assert report["problem_clusters"]
    assert report["opportunity_queue"]
    assert report["top_opportunities"][0]["scores"]["overall_score"] >= report["top_opportunities"][-1]["scores"]["overall_score"]
