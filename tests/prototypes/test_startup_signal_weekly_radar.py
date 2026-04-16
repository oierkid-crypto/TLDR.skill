from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from db import init_db, save_daily_report  # type: ignore  # noqa: E402
from weekly_radar import run_weekly_radar  # type: ignore  # noqa: E402


def test_run_weekly_radar_summarizes_prior_daily_reports_and_honest_empty_channels(tmp_path: Path) -> None:
    db_path = tmp_path / "radar.db"
    init_db(db_path)

    save_daily_report(
        db_path,
        {
            "report_date": "2026-04-14",
            "channels": {
                "2b": {
                    "strong_signals": [
                        {
                            "signal_id": "2b:crm_updates",
                            "title": "Users want CRM updates automated",
                            "summary": "Manual CRM updates are recurring workflow pain.",
                            "assessment": {
                                "frequency_count": 3,
                                "cross_platform": True,
                                "platforms": ["reddit", "x"],
                                "real_need_judgment": "credible",
                                "real_need_confidence": 0.84,
                                "why_it_seems_real": ["repeated workflow pain"],
                            },
                            "evidence": [
                                {
                                    "platform": "reddit",
                                    "content": "Need a tool to automate CRM updates.",
                                    "excerpt": "automate CRM updates",
                                    "url": "https://reddit.example/post/1",
                                }
                            ],
                        }
                    ],
                    "weak_or_monitor_only": [],
                    "no_strong_signal_message": None,
                },
                "2c": {
                    "strong_signals": [],
                    "weak_or_monitor_only": [],
                    "no_strong_signal_message": "No sufficiently strong 2C signal was detected today.",
                },
                "2p": {
                    "strong_signals": [],
                    "weak_or_monitor_only": [],
                    "no_strong_signal_message": "No sufficiently strong 2P signal was detected today.",
                },
            },
        },
    )
    save_daily_report(
        db_path,
        {
            "report_date": "2026-04-15",
            "channels": {
                "2b": {
                    "strong_signals": [
                        {
                            "signal_id": "2b:crm_updates",
                            "title": "Users want CRM updates automated",
                            "summary": "Manual CRM updates are recurring workflow pain.",
                            "assessment": {
                                "frequency_count": 2,
                                "cross_platform": False,
                                "platforms": ["x"],
                                "real_need_judgment": "credible",
                                "real_need_confidence": 0.7,
                                "why_it_seems_real": ["repeated workflow pain"],
                            },
                            "evidence": [
                                {
                                    "platform": "x",
                                    "content": "Still manually updating CRM after each call.",
                                    "excerpt": "manually updating CRM",
                                    "url": "https://x.com/example/1",
                                }
                            ],
                        }
                    ],
                    "weak_or_monitor_only": [],
                    "no_strong_signal_message": None,
                },
                "2c": {
                    "strong_signals": [],
                    "weak_or_monitor_only": [],
                    "no_strong_signal_message": "No sufficiently strong 2C signal was detected today.",
                },
                "2p": {
                    "strong_signals": [],
                    "weak_or_monitor_only": [],
                    "no_strong_signal_message": "No sufficiently strong 2P signal was detected today.",
                },
            },
        },
    )

    weekly = run_weekly_radar(
        week_label="2026-W16",
        start_date="2026-04-14",
        end_date="2026-04-20",
        db_path=db_path,
    )

    assert weekly["week_label"] == "2026-W16"
    assert "CRM" in weekly["overall_summary"] or "crm" in weekly["overall_summary"].lower()
    assert weekly["channels"]["2b"]["strongest_patterns"]
    assert weekly["channels"]["2b"]["representative_evidence"]
    assert weekly["channels"]["2c"]["no_strong_signal_message"]
    assert weekly["channels"]["2p"]["no_strong_signal_message"]
