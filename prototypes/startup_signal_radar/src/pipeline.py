from __future__ import annotations

from pathlib import Path

from cluster import cluster_signals, cluster_to_problem_cluster
from extract import extract_signal
from normalize import normalize_reddit_post, normalize_x_post, normalize_xiaohongshu_post
from opportunity import score_opportunity
from reports import build_daily_report
from sources import load_fixture_source
from state_store import load_snapshot, save_snapshot, snapshot_cluster_index
from watchlist import build_watchlist, summarize_trends


NORMALIZERS = {
    "reddit": normalize_reddit_post,
    "x": normalize_x_post,
    "xiaohongshu": normalize_xiaohongshu_post,
}

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"
DEFAULT_STATE_DIR = PROJECT_ROOT / "state"


def _normalize_fixture_record(record: dict) -> object:
    platform = record["platform"]
    normalizer = NORMALIZERS[platform]
    return normalizer(record["raw"])


def latest_snapshot_path(state_dir: str | Path = DEFAULT_STATE_DIR) -> Path | None:
    candidates = sorted(Path(state_dir).glob("fixture_snapshot.*.json"))
    return candidates[-1] if candidates else None


def _report_output_path(report_date: str, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> Path:
    return Path(output_dir) / f"fixture_report.{report_date}.json"


def _snapshot_output_path(report_date: str, state_dir: str | Path = DEFAULT_STATE_DIR) -> Path:
    return Path(state_dir) / f"fixture_snapshot.{report_date}.json"


def run_fixture_pipeline(
    platforms: list[str],
    report_date: str,
    previous_snapshot_path: str | Path | None = None,
) -> dict:
    normalized_posts = []
    signals = []
    for platform in platforms:
        for record in load_fixture_source(platform):
            post = _normalize_fixture_record(record)
            normalized_posts.append(post)
            signals.append(extract_signal(post))

    clusters = cluster_signals(signals)
    problem_clusters = [cluster_to_problem_cluster(cluster) for cluster in clusters]
    scored_opportunities = [score_opportunity(signal) for signal in signals]
    report = build_daily_report(scored_opportunities, report_date=report_date)
    report["problem_clusters"] = problem_clusters
    report["normalized_posts"] = [post.model_dump() for post in normalized_posts]
    report["watchlist"] = build_watchlist(problem_clusters)

    if previous_snapshot_path:
        previous = load_snapshot(previous_snapshot_path)
        previous_index = snapshot_cluster_index(previous)
        current_index = snapshot_cluster_index({"problem_clusters": problem_clusters})
        report["trend_summary"] = summarize_trends(previous_index, current_index)
    else:
        report["trend_summary"] = {"rising": [], "stable_or_down": []}

    return report


def run_and_persist_fixture_pipeline(
    platforms: list[str],
    report_date: str,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    state_dir: str | Path = DEFAULT_STATE_DIR,
    previous_snapshot_path: str | Path | None = None,
) -> dict:
    resolved_previous_snapshot = Path(previous_snapshot_path) if previous_snapshot_path else latest_snapshot_path(state_dir)
    report = run_fixture_pipeline(
        platforms=platforms,
        report_date=report_date,
        previous_snapshot_path=resolved_previous_snapshot,
    )

    report_path = _report_output_path(report_date, output_dir)
    snapshot_path = _snapshot_output_path(report_date, state_dir)
    snapshot = {
        "report_date": report_date,
        "problem_clusters": report["problem_clusters"],
        "watchlist": report["watchlist"],
        "trend_summary": report["trend_summary"],
    }

    save_snapshot(report, report_path)
    save_snapshot(snapshot, snapshot_path)

    return {
        "report": report,
        "report_path": str(report_path),
        "snapshot_path": str(snapshot_path),
        "previous_snapshot_path": str(resolved_previous_snapshot) if resolved_previous_snapshot else None,
    }
