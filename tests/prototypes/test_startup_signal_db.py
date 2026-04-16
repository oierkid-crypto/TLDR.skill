from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from db import (  # type: ignore  # noqa: E402
    build_canonical_evidence_id,
    init_db,
    insert_evidence,
    insert_search_hits,
    insert_search_runs,
    insert_signals,
    load_daily_reports_between,
    load_signals_for_date,
    save_daily_report,
    save_weekly_report,
)


def test_init_db_creates_expected_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "radar.db"

    init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = {row[0] for row in rows}
    assert {
        "evidence",
        "signals",
        "daily_signal_snapshots",
        "search_runs",
        "search_hits",
        "daily_reports",
        "weekly_reports",
    }.issubset(table_names)


def test_evidence_upsert_is_cross_day_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "radar.db"
    init_db(db_path)

    canonical_id = build_canonical_evidence_id("reddit", "abc123")
    first = {
        "canonical_evidence_id": canonical_id,
        "platform": "reddit",
        "source_native_id": "abc123",
        "channel": "2b",
        "author_handle": "alice",
        "url": "https://reddit.example/post/abc123",
        "content_raw": "Manual CRM updates are exhausting.",
        "content_normalized": "manual crm updates are exhausting.",
        "published_at": "2026-04-15T10:00:00Z",
        "seen_at": "2026-04-16T19:00:00Z",
        "run_id": "run-1",
        "report_date": "2026-04-16",
    }
    second = {
        **first,
        "seen_at": "2026-04-17T19:00:00Z",
        "run_id": "run-2",
        "report_date": "2026-04-17",
    }

    insert_evidence(db_path, [first])
    insert_evidence(db_path, [second])

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT canonical_evidence_id, first_seen_at, last_seen_at, first_seen_run_id, last_seen_run_id, hit_count_total FROM evidence"
        ).fetchone()
        total = conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]

    assert total == 1
    assert row == (
        canonical_id,
        "2026-04-16T19:00:00Z",
        "2026-04-17T19:00:00Z",
        "run-1",
        "run-2",
        2,
    )


def test_search_hits_keep_query_duplicates_but_evidence_does_not(tmp_path: Path) -> None:
    db_path = tmp_path / "radar.db"
    init_db(db_path)

    canonical_id = build_canonical_evidence_id("x", "tweet-1")
    insert_search_runs(
        db_path,
        [
            {
                "run_id": "run-a",
                "report_date": "2026-04-16",
                "platform": "x",
                "channel": "2b",
                "query_text": "crm manual update",
                "lookback_hours": 36,
                "limit_count": 20,
                "started_at": "2026-04-16T19:00:00Z",
                "finished_at": "2026-04-16T19:00:01Z",
                "raw_hit_count": 1,
                "unique_hit_count": 1,
                "status": "success",
            },
            {
                "run_id": "run-b",
                "report_date": "2026-04-16",
                "platform": "x",
                "channel": "2b",
                "query_text": "hubspot alternative",
                "lookback_hours": 36,
                "limit_count": 20,
                "started_at": "2026-04-16T19:01:00Z",
                "finished_at": "2026-04-16T19:01:01Z",
                "raw_hit_count": 1,
                "unique_hit_count": 1,
                "status": "success",
            },
        ],
    )
    insert_search_hits(
        db_path,
        [
            {
                "hit_id": "hit-1",
                "run_id": "run-a",
                "canonical_evidence_id": canonical_id,
                "source_native_id": "tweet-1",
                "platform": "x",
                "report_date": "2026-04-16",
                "rank_in_response": 1,
            },
            {
                "hit_id": "hit-2",
                "run_id": "run-b",
                "canonical_evidence_id": canonical_id,
                "source_native_id": "tweet-1",
                "platform": "x",
                "report_date": "2026-04-16",
                "rank_in_response": 3,
            },
        ],
    )
    insert_evidence(
        db_path,
        [
            {
                "canonical_evidence_id": canonical_id,
                "platform": "x",
                "source_native_id": "tweet-1",
                "channel": "2b",
                "author_handle": "bob",
                "url": "https://x.example/tweet/1",
                "content_raw": "Need a tool that updates CRM automatically.",
                "content_normalized": "need a tool that updates crm automatically.",
                "published_at": "2026-04-16T10:00:00Z",
                "seen_at": "2026-04-16T19:00:00Z",
                "run_id": "run-a",
                "report_date": "2026-04-16",
            },
            {
                "canonical_evidence_id": canonical_id,
                "platform": "x",
                "source_native_id": "tweet-1",
                "channel": "2b",
                "author_handle": "bob",
                "url": "https://x.example/tweet/1",
                "content_raw": "Need a tool that updates CRM automatically.",
                "content_normalized": "need a tool that updates crm automatically.",
                "published_at": "2026-04-16T10:00:00Z",
                "seen_at": "2026-04-16T19:05:00Z",
                "run_id": "run-b",
                "report_date": "2026-04-16",
            },
        ],
    )

    with sqlite3.connect(db_path) as conn:
        hit_count = conn.execute("SELECT COUNT(*) FROM search_hits").fetchone()[0]
        evidence_count = conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
        total_hits = conn.execute("SELECT hit_count_total FROM evidence WHERE canonical_evidence_id = ?", (canonical_id,)).fetchone()[0]

    assert hit_count == 2
    assert evidence_count == 1
    assert total_hits == 2


def test_signal_snapshots_preserve_history_across_days(tmp_path: Path) -> None:
    db_path = tmp_path / "radar.db"
    init_db(db_path)

    insert_signals(
        db_path,
        [
            {
                "signal_key": "2b:crm_updates",
                "report_date": "2026-04-16",
                "channel": "2b",
                "title": "CRM sync pain",
                "payload": {"signal_id": "2b:crm_updates", "frequency_count": 2},
            },
            {
                "signal_key": "2b:crm_updates",
                "report_date": "2026-04-17",
                "channel": "2b",
                "title": "CRM sync pain",
                "payload": {"signal_id": "2b:crm_updates", "frequency_count": 3},
            },
        ],
    )

    day_one = load_signals_for_date(db_path, "2026-04-16")
    day_two = load_signals_for_date(db_path, "2026-04-17")

    with sqlite3.connect(db_path) as conn:
        snapshot_count = conn.execute("SELECT COUNT(*) FROM daily_signal_snapshots").fetchone()[0]
        latest_count = conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0]

    assert snapshot_count == 2
    assert latest_count == 1
    assert day_one[0]["payload"]["frequency_count"] == 2
    assert day_two[0]["payload"]["frequency_count"] == 3


def test_init_db_migrates_legacy_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE evidence (
                evidence_id TEXT PRIMARY KEY,
                report_date TEXT NOT NULL,
                platform TEXT NOT NULL,
                channel TEXT NOT NULL,
                content TEXT NOT NULL,
                url TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE signals (
                signal_id TEXT PRIMARY KEY,
                report_date TEXT NOT NULL,
                channel TEXT NOT NULL,
                title TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO evidence VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "2026-04-16:reddit:post-1",
                "2026-04-16",
                "reddit",
                "2b",
                "Manual CRM updates are exhausting.",
                "https://reddit.example/post/1",
                "{}",
            ),
        )
        conn.execute(
            "INSERT INTO signals VALUES (?, ?, ?, ?, ?)",
            ("2b:crm_updates", "2026-04-16", "2b", "CRM sync pain", '{"signal_id": "2b:crm_updates"}'),
        )

    init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        evidence_columns = {row[1] for row in conn.execute("PRAGMA table_info(evidence)")}
        signal_columns = {row[1] for row in conn.execute("PRAGMA table_info(signals)")}
        evidence_count = conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
        snapshot_count = conn.execute("SELECT COUNT(*) FROM daily_signal_snapshots").fetchone()[0]

    assert "canonical_evidence_id" in evidence_columns
    assert "source_native_id" in evidence_columns
    assert "signal_key" in signal_columns
    assert evidence_count == 1
    assert snapshot_count == 1


def test_insert_and_load_signal_and_report_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "radar.db"
    init_db(db_path)

    insert_evidence(
        db_path,
        [
            {
                "canonical_evidence_id": build_canonical_evidence_id("reddit", "post-1"),
                "platform": "reddit",
                "source_native_id": "post-1",
                "channel": "2b",
                "author_handle": "alice",
                "url": "https://reddit.example/post/1",
                "content_raw": "Users complain about manual CRM updates after calls.",
                "content_normalized": "users complain about manual crm updates after calls.",
                "published_at": "2026-04-16T09:00:00Z",
                "seen_at": "2026-04-16T19:00:00Z",
                "run_id": "run-1",
                "report_date": "2026-04-16",
            }
        ],
    )
    insert_signals(
        db_path,
        [
            {
                "signal_key": "sig1",
                "report_date": "2026-04-16",
                "channel": "2b",
                "title": "CRM sync pain",
                "payload": {"signal_id": "sig1", "frequency_count": 2, "cross_platform": False},
            }
        ],
    )
    save_daily_report(
        db_path,
        {
            "report_date": "2026-04-16",
            "channels": {
                "2b": {"strong_signals": [{"signal_id": "sig1"}]},
                "2c": {"strong_signals": []},
                "2p": {"strong_signals": []},
            },
        },
    )
    save_weekly_report(
        db_path,
        {
            "week_label": "2026-W16",
            "overall_summary": "2B stood out.",
            "channels": {"2b": {}, "2c": {}, "2p": {}},
        },
    )

    loaded_signals = load_signals_for_date(db_path, "2026-04-16")
    loaded_reports = load_daily_reports_between(db_path, "2026-04-14", "2026-04-20")

    assert loaded_signals[0]["signal_id"] == "sig1"
    assert loaded_signals[0]["payload"]["frequency_count"] == 2
    assert loaded_reports[0]["report_date"] == "2026-04-16"
    assert loaded_reports[0]["channels"]["2b"]["strong_signals"][0]["signal_id"] == "sig1"
