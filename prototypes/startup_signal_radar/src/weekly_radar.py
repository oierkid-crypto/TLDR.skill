from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from db import load_daily_reports_between, save_weekly_report
from report_models import ChannelWeeklyReport, WeeklyNeedsReport

CHANNELS = ("2b", "2c", "2p")


def run_weekly_radar(week_label: str, start_date: str, end_date: str, db_path: str | Path) -> dict:
    daily_reports = load_daily_reports_between(db_path, start_date, end_date)
    channel_buckets: dict[str, list[dict]] = {channel: [] for channel in CHANNELS}
    for report in daily_reports:
        for channel in CHANNELS:
            channel_buckets[channel].extend(report.get("channels", {}).get(channel, {}).get("strong_signals", []))

    channels_payload: dict[str, dict] = {}
    strongest_titles: list[str] = []
    for channel, items in channel_buckets.items():
        if not items:
            channels_payload[channel] = ChannelWeeklyReport(
                strongest_patterns=[],
                representative_evidence=[],
                no_strong_signal_message=f"本周没有发现足够强的 {channel.upper()} 持续性信号。",
            ).model_dump()
            continue

        grouped: dict[str, list[dict]] = defaultdict(list)
        for item in items:
            grouped[item["signal_id"]].append(item)

        ranked = sorted(grouped.values(), key=lambda group: (len(group), sum(x.get("assessment", {}).get("frequency_count", 0) for x in group)), reverse=True)
        top_group = ranked[0]
        top_item = top_group[0]
        strongest_titles.append(top_item["title"])
        representative_evidence = []
        for occurrence in top_group[:3]:
            representative_evidence.extend(e.get("excerpt") or e.get("content") for e in occurrence.get("evidence", [])[:1])
        channels_payload[channel] = ChannelWeeklyReport(
            strongest_patterns=[
                f"{top_item['title']} 在本周 {len(top_group)} 份日报中重复出现，单日最高出现频率为 {max(x.get('assessment', {}).get('frequency_count', 0) for x in top_group)}。"
            ],
            representative_evidence=representative_evidence[:3],
            no_strong_signal_message=None,
        ).model_dump()

    overall_summary = (
        f"本周最清晰的重复性需求包括：{', '.join(strongest_titles)}。"
        if strongest_titles
        else "本周在跟踪频道中没有发现足够强的持续性需求。"
    )
    report = WeeklyNeedsReport(week_label=week_label, overall_summary=overall_summary, channels={k: ChannelWeeklyReport(**v) for k, v in channels_payload.items()}).model_dump()
    save_weekly_report(db_path, report)
    return report
