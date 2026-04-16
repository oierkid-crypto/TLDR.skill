from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from uuid import uuid4

from channel_router import classify_channel_from_signal
from db import (
    build_canonical_evidence_id,
    insert_evidence,
    insert_search_hits,
    insert_search_runs,
    insert_signals,
    save_daily_report,
)
from extract import extract_signal
from normalize import normalize_reddit_post, normalize_x_post
from query_builder import load_taxonomy
from report_models import ChannelDailyReport, DailyNeedsReport, EvidenceItem, SignalAssessment, SignalItem
from score import weighted_overall_score
from sources import load_fixture_source

NORMALIZERS = {
    "reddit": lambda raw: normalize_reddit_post(raw),
    "x": lambda raw: normalize_x_post(raw),
}
CHANNELS = ("2b", "2c", "2p")
DEFAULT_LOOKBACK_HOURS = 36
DEFAULT_RESULTS_PER_QUERY = 20


def _assessment_for_group(signals: list) -> SignalAssessment:
    platforms = sorted({signal.normalized_post.platform for signal in signals})
    frequency_count = len(signals)
    cross_platform = len(platforms) >= 2
    why = []
    if frequency_count >= 2:
        why.append("repeated mentions")
    if cross_platform:
        why.append("cross-platform evidence")
    if any(signal.replacement_intent for signal in signals):
        why.append("explicit tool-seeking intent")
    if any(signal.workflow for signal in signals):
        why.append("concrete workflow friction")
    credible = frequency_count >= 2 or cross_platform
    confidence = min(
        0.95,
        0.2
        + 0.2 * frequency_count
        + (0.2 if cross_platform else 0.0)
        + (0.1 if any(signal.replacement_intent for signal in signals) else 0.0)
        + (0.1 if any(signal.workflow for signal in signals) else 0.0),
    )
    return SignalAssessment(
        frequency_count=frequency_count,
        cross_platform=cross_platform,
        platforms=platforms,
        real_need_judgment="credible" if credible else "weak",
        real_need_confidence=round(confidence, 2),
        why_it_seems_real=why,
    )


def _group_key(signal) -> str:
    return signal.workflow or signal.normalized_post.title or signal.normalized_post.post_id


def run_daily_radar(
    report_date: str,
    db_path: str | Path,
    taxonomy_path: str,
    platforms: list[str] | None = None,
) -> dict:
    selected_platforms = platforms or ["reddit", "x"]
    taxonomy = load_taxonomy(taxonomy_path)
    channel_groups: dict[str, dict[str, list]] = {channel: {} for channel in CHANNELS}
    evidence_rows: list[dict] = []
    search_run_rows: list[dict] = []
    search_hit_rows: list[dict] = []
    run_counters: dict[tuple[str, str], int] = defaultdict(int)
    run_ids: dict[tuple[str, str], str] = {}

    for platform in selected_platforms:
        if platform not in NORMALIZERS:
            continue
        for record in load_fixture_source(platform):
            post = NORMALIZERS[platform](record["raw"])
            signal = extract_signal(post)
            channel = classify_channel_from_signal(signal, taxonomy)
            if not channel:
                continue

            run_key = (platform, channel)
            if run_key not in run_ids:
                run_id = f"{report_date}:{platform}:{channel}:{uuid4().hex[:8]}"
                run_ids[run_key] = run_id
                search_run_rows.append(
                    {
                        "run_id": run_id,
                        "report_date": report_date,
                        "platform": platform,
                        "channel": channel,
                        "query_text": f"fixture::{platform}::{channel}",
                        "lookback_hours": DEFAULT_LOOKBACK_HOURS,
                        "limit_count": DEFAULT_RESULTS_PER_QUERY,
                        "started_at": f"{report_date}T19:00:00Z",
                        "finished_at": f"{report_date}T19:00:00Z",
                        "raw_hit_count": 0,
                        "unique_hit_count": 0,
                        "status": "success",
                    }
                )
            run_id = run_ids[run_key]
            run_counters[run_key] += 1

            channel_groups[channel].setdefault(_group_key(signal), []).append(signal)
            canonical_evidence_id = build_canonical_evidence_id(post.platform, post.post_id)
            search_hit_rows.append(
                {
                    "hit_id": f"{run_id}:{canonical_evidence_id}:{run_counters[run_key]}",
                    "run_id": run_id,
                    "canonical_evidence_id": canonical_evidence_id,
                    "source_native_id": post.post_id,
                    "platform": post.platform,
                    "report_date": report_date,
                    "rank_in_response": run_counters[run_key],
                }
            )
            evidence_rows.append(
                {
                    "canonical_evidence_id": canonical_evidence_id,
                    "platform": post.platform,
                    "source_native_id": post.post_id,
                    "report_date": report_date,
                    "channel": channel,
                    "author_handle": post.author_handle,
                    "content_raw": post.raw_text,
                    "content_normalized": post.raw_text.lower(),
                    "published_at": post.created_at,
                    "seen_at": f"{report_date}T19:00:00Z",
                    "run_id": run_id,
                    "url": post.url,
                }
            )

    for row in search_run_rows:
        run_key = (row["platform"], row["channel"])
        run_hits = [hit for hit in search_hit_rows if hit["run_id"] == row["run_id"]]
        row["raw_hit_count"] = len(run_hits)
        row["unique_hit_count"] = len({hit["canonical_evidence_id"] for hit in run_hits})

    signal_rows: list[dict] = []
    channels_payload: dict[str, dict] = {}

    for channel in CHANNELS:
        grouped = channel_groups[channel]
        strong_signals: list[SignalItem] = []
        weak_signals: list[SignalItem] = []
        ranked_items = []
        for key, signals in grouped.items():
            assessment = _assessment_for_group(signals)
            evidence = [
                EvidenceItem(
                    platform=signal.normalized_post.platform,
                    content=signal.normalized_post.raw_text,
                    excerpt=signal.evidence_excerpt,
                    url=signal.normalized_post.url,
                )
                for signal in signals
            ]
            title = signals[0].normalized_post.title or (signals[0].workflow or key)
            summary = f"共发现 {assessment.frequency_count} 条证据，指向 {signals[0].workflow or key} 这一重复性需求。"
            signal_key = f"{channel}:{key.replace(' ', '_')}"
            item = SignalItem(
                signal_id=signal_key,
                title=title,
                summary=summary,
                channel=channel,
                evidence=evidence,
                assessment=assessment,
            )
            score = weighted_overall_score(
                pain_score=min(10.0, 5.0 + assessment.frequency_count),
                buildability_score=8.0,
                ai_leverage_score=8.5 if any(signal.ai_fit for signal in signals) else 5.0,
                distribution_fit_score=8.0 if assessment.cross_platform else 6.0,
                business_quality_score=8.0 if any(signal.replacement_intent for signal in signals) else 6.0,
            )
            ranked_items.append((score, item))
            signal_rows.append(
                {
                    "signal_key": signal_key,
                    "report_date": report_date,
                    "channel": channel,
                    "title": item.title,
                    "payload": item.model_dump(),
                }
            )

        for _, item in sorted(ranked_items, key=lambda pair: pair[0], reverse=True):
            if item.assessment.real_need_judgment == "credible":
                strong_signals.append(item)
            else:
                weak_signals.append(item)

        channel_report = ChannelDailyReport(
            strong_signals=strong_signals,
            weak_or_monitor_only=weak_signals,
            no_strong_signal_message=None if strong_signals else f"今天没有发现足够强的 {channel.upper()} 信号。",
        )
        channels_payload[channel] = channel_report.model_dump()

    report = DailyNeedsReport(report_date=report_date, channels={k: ChannelDailyReport(**v) for k, v in channels_payload.items()}).model_dump()
    insert_search_runs(db_path, search_run_rows)
    insert_search_hits(db_path, search_hit_rows)
    insert_evidence(db_path, evidence_rows)
    insert_signals(db_path, signal_rows)
    save_daily_report(db_path, report)
    return report
