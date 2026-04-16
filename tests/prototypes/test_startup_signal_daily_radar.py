from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from db import init_db, load_signals_for_date  # type: ignore  # noqa: E402
from daily_radar import run_daily_radar  # type: ignore  # noqa: E402
from report_writer import render_daily_user_needs_report, render_weekly_user_needs_report  # type: ignore  # noqa: E402
from report_models import (  # type: ignore  # noqa: E402
    ChannelDailyReport,
    ChannelWeeklyReport,
    DailyNeedsReport,
    EvidenceItem,
    SignalAssessment,
    SignalItem,
    WeeklyNeedsReport,
)
from weekly_radar import run_weekly_radar  # type: ignore  # noqa: E402


def test_daily_report_models_include_2b_2c_2p_channels_and_signal_assessment() -> None:
    evidence = EvidenceItem(
        platform="reddit",
        content="Users keep complaining that updating CRM after calls is repetitive.",
        excerpt="updating CRM after calls is repetitive",
        url="https://reddit.example/post/1",
    )
    assessment = SignalAssessment(
        frequency_count=3,
        cross_platform=True,
        platforms=["reddit", "x"],
        real_need_judgment="credible",
        real_need_confidence=0.84,
        why_it_seems_real=["repeated workflow pain", "cross-platform repetition"],
    )
    signal = SignalItem(
        signal_id="signal_crm_sync",
        title="Users want CRM updates automated",
        summary="Manual CRM updates are recurring workflow pain.",
        channel="2b",
        evidence=[evidence],
        assessment=assessment,
    )
    channel = ChannelDailyReport(
        strong_signals=[signal],
        weak_or_monitor_only=[],
        no_strong_signal_message=None,
    )

    report = DailyNeedsReport(
        report_date="2026-04-16",
        channels={"2b": channel, "2c": ChannelDailyReport(), "2p": ChannelDailyReport()},
    )

    dumped = report.model_dump()
    assert dumped["report_date"] == "2026-04-16"
    assert set(dumped["channels"].keys()) == {"2b", "2c", "2p"}
    assert dumped["channels"]["2b"]["strong_signals"][0]["assessment"]["frequency_count"] == 3
    assert dumped["channels"]["2b"]["strong_signals"][0]["assessment"]["cross_platform"] is True


def test_weekly_report_models_include_overall_summary_and_channels() -> None:
    weekly = WeeklyNeedsReport(
        week_label="2026-W16",
        overall_summary="2B CRM automation remained the clearest repeated need this week.",
        channels={
            "2b": ChannelWeeklyReport(
                strongest_patterns=["CRM automation demand repeated across multiple days"],
                representative_evidence=["Need a tool to automate CRM updates."],
                no_strong_signal_message=None,
            ),
            "2c": ChannelWeeklyReport(
                strongest_patterns=[],
                representative_evidence=[],
                no_strong_signal_message="No sufficiently strong consumer need was detected this week.",
            ),
            "2p": ChannelWeeklyReport(
                strongest_patterns=[],
                representative_evidence=[],
                no_strong_signal_message="No sufficiently strong prosumer need was detected this week.",
            ),
        },
    )

    dumped = weekly.model_dump()
    assert dumped["week_label"] == "2026-W16"
    assert "overall_summary" in dumped
    assert set(dumped["channels"].keys()) == {"2b", "2c", "2p"}
    assert dumped["channels"]["2c"]["no_strong_signal_message"]


def test_run_daily_radar_persists_signals_and_surfaces_broader_2b_2c_2p_coverage(tmp_path: Path) -> None:
    db_path = tmp_path / "radar.db"
    init_db(db_path)

    report = run_daily_radar(
        report_date="2026-04-16",
        db_path=db_path,
        taxonomy_path="prototypes/startup_signal_radar/config/query_taxonomy.example.yaml",
        platforms=["reddit", "x"],
    )

    assert set(report["channels"].keys()) == {"2b", "2c", "2p"}

    b2b_signal = report["channels"]["2b"]["strong_signals"][0]
    assert b2b_signal["evidence"]
    assert b2b_signal["assessment"]["frequency_count"] >= 2
    assert b2b_signal["assessment"]["cross_platform"] is True
    assert set(b2b_signal["assessment"]["platforms"]) == {"reddit", "x"}
    assert b2b_signal["assessment"]["real_need_judgment"] == "credible"

    assert report["channels"]["2c"]["strong_signals"]
    assert report["channels"]["2p"]["strong_signals"]
    b2c_signal = report["channels"]["2c"]["strong_signals"][0]
    b2p_signal = report["channels"]["2p"]["strong_signals"][0]
    assert b2c_signal["assessment"]["frequency_count"] >= 2
    assert b2p_signal["assessment"]["frequency_count"] >= 2
    assert b2c_signal["assessment"]["cross_platform"] is True
    assert b2p_signal["assessment"]["cross_platform"] is True
    assert report["channels"]["2c"]["no_strong_signal_message"] is None
    assert report["channels"]["2p"]["no_strong_signal_message"] is None

    stored_signals = load_signals_for_date(db_path, "2026-04-16")
    assert len(stored_signals) >= 3


def test_report_writer_renders_user_needs_first_daily_and_weekly_text(tmp_path: Path) -> None:
    db_path = tmp_path / "radar.db"
    init_db(db_path)
    daily = run_daily_radar(
        report_date="2026-04-16",
        db_path=db_path,
        taxonomy_path="prototypes/startup_signal_radar/config/query_taxonomy.example.yaml",
        platforms=["reddit", "x"],
    )
    weekly = run_weekly_radar(
        week_label="2026-W16",
        start_date="2026-04-14",
        end_date="2026-04-20",
        db_path=db_path,
    )

    daily_text = render_daily_user_needs_report(daily)
    weekly_text = render_weekly_user_needs_report(weekly)

    assert "2B" in daily_text and "2C" in daily_text and "2P" in daily_text
    assert "2B" in weekly_text and "2C" in weekly_text and "2P" in weekly_text
    assert "Evidence（原文）" in daily_text
    assert "结构化判断" in daily_text
    assert "pipeline" not in daily_text.lower()
    assert "fixture" not in daily_text.lower()
    assert "engineering progress" not in daily_text.lower()
