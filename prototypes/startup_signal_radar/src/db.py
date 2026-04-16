from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any


EVIDENCE_COLUMN_DEFS = {
    "canonical_evidence_id": "TEXT",
    "platform": "TEXT",
    "source_native_id": "TEXT",
    "channel": "TEXT",
    "author_handle": "TEXT",
    "url": "TEXT",
    "content_raw": "TEXT",
    "content_normalized": "TEXT",
    "published_at": "TEXT",
    "first_seen_at": "TEXT",
    "last_seen_at": "TEXT",
    "first_seen_run_id": "TEXT",
    "last_seen_run_id": "TEXT",
    "first_seen_report_date": "TEXT",
    "last_seen_report_date": "TEXT",
    "hit_count_total": "INTEGER NOT NULL DEFAULT 1",
    "payload_json": "TEXT",
}

SIGNALS_COLUMN_DEFS = {
    "signal_key": "TEXT",
    "latest_report_date": "TEXT",
    "channel": "TEXT",
    "title": "TEXT",
    "payload_json": "TEXT",
}


def _connect(db_path: str | Path) -> sqlite3.Connection:
    return sqlite3.connect(Path(db_path))


def build_canonical_evidence_id(platform: str, source_native_id: str) -> str:
    return hashlib.sha256(f"{platform}|{source_native_id}".encode("utf-8")).hexdigest()


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}


def _ensure_columns(conn: sqlite3.Connection, table_name: str, column_defs: dict[str, str]) -> set[str]:
    existing = _table_columns(conn, table_name)
    for column_name, column_def in column_defs.items():
        if column_name not in existing:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
    return _table_columns(conn, table_name)


def _legacy_source_native_id(legacy_evidence_id: str | None, url: str | None) -> str:
    if legacy_evidence_id and ":" in legacy_evidence_id:
        return legacy_evidence_id.split(":")[-1]
    if legacy_evidence_id:
        return legacy_evidence_id
    return url or "unknown"


def _backfill_legacy_evidence(conn: sqlite3.Connection) -> None:
    columns = _table_columns(conn, "evidence")
    if "evidence_id" not in columns:
        return

    legacy_rows = conn.execute(
        "SELECT rowid, evidence_id, report_date, platform, channel, content, url, payload_json FROM evidence"
    ).fetchall()
    for rowid, evidence_id, report_date, platform, channel, content, url, payload_json in legacy_rows:
        source_native_id = _legacy_source_native_id(evidence_id, url)
        canonical_evidence_id = build_canonical_evidence_id(platform or "unknown", source_native_id)
        seen_at = f"{report_date}T00:00:00" if report_date else "unknown"
        conn.execute(
            """
            UPDATE evidence
            SET canonical_evidence_id = COALESCE(canonical_evidence_id, ?),
                source_native_id = COALESCE(source_native_id, ?),
                author_handle = COALESCE(author_handle, NULL),
                content_raw = COALESCE(content_raw, content, ''),
                content_normalized = COALESCE(content_normalized, lower(COALESCE(content, ''))),
                published_at = COALESCE(published_at, report_date, ''),
                first_seen_at = COALESCE(first_seen_at, ?, ''),
                last_seen_at = COALESCE(last_seen_at, ?, ''),
                first_seen_report_date = COALESCE(first_seen_report_date, report_date, ''),
                last_seen_report_date = COALESCE(last_seen_report_date, report_date, ''),
                hit_count_total = COALESCE(hit_count_total, 1),
                payload_json = COALESCE(payload_json, '{}'),
                channel = COALESCE(channel, ?),
                url = COALESCE(url, ?),
                platform = COALESCE(platform, ?)
            WHERE rowid = ?
            """,
            (canonical_evidence_id, source_native_id, seen_at, seen_at, channel or "unknown", url or "", platform or "unknown", rowid),
        )


def _backfill_legacy_signals(conn: sqlite3.Connection) -> None:
    columns = _table_columns(conn, "signals")
    if "signal_id" not in columns:
        return

    legacy_rows = conn.execute(
        "SELECT rowid, signal_id, report_date, channel, title, payload_json FROM signals"
    ).fetchall()
    for rowid, signal_id, report_date, channel, title, payload_json in legacy_rows:
        conn.execute(
            """
            UPDATE signals
            SET signal_key = COALESCE(signal_key, ?),
                latest_report_date = COALESCE(latest_report_date, report_date, ?),
                channel = COALESCE(channel, ?),
                title = COALESCE(title, ?),
                payload_json = COALESCE(payload_json, '{}')
            WHERE rowid = ?
            """,
            (signal_id, report_date or "", channel or "unknown", title or signal_id or "unknown", rowid),
        )


def _migrate_existing_schema(conn: sqlite3.Connection) -> None:
    if _table_exists(conn, "evidence"):
        _ensure_columns(conn, "evidence", EVIDENCE_COLUMN_DEFS)
        _backfill_legacy_evidence(conn)

    if _table_exists(conn, "signals"):
        _ensure_columns(conn, "signals", SIGNALS_COLUMN_DEFS)
        _backfill_legacy_signals(conn)


def _create_evidence_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence (
            canonical_evidence_id TEXT PRIMARY KEY,
            platform TEXT NOT NULL,
            source_native_id TEXT NOT NULL,
            channel TEXT NOT NULL,
            author_handle TEXT,
            url TEXT NOT NULL,
            content_raw TEXT NOT NULL,
            content_normalized TEXT NOT NULL,
            published_at TEXT NOT NULL,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            first_seen_run_id TEXT,
            last_seen_run_id TEXT,
            first_seen_report_date TEXT NOT NULL,
            last_seen_report_date TEXT NOT NULL,
            hit_count_total INTEGER NOT NULL DEFAULT 1,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_evidence_platform_native ON evidence(platform, source_native_id)"
    )


def _create_signal_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS signals (
            signal_key TEXT PRIMARY KEY,
            latest_report_date TEXT NOT NULL,
            channel TEXT NOT NULL,
            title TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_signal_snapshots (
            report_date TEXT NOT NULL,
            signal_key TEXT NOT NULL,
            channel TEXT NOT NULL,
            title TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (report_date, signal_key)
        )
        """
    )


def _migrate_legacy_evidence(conn: sqlite3.Connection) -> None:
    columns = _table_columns(conn, "evidence")
    if not columns or "canonical_evidence_id" in columns:
        return
    legacy_rows = conn.execute(
        "SELECT evidence_id, report_date, platform, channel, content, url, payload_json FROM evidence"
    ).fetchall()
    conn.execute("ALTER TABLE evidence RENAME TO evidence_legacy")
    _create_evidence_table(conn)
    for evidence_id, report_date, platform, channel, content, url, payload_json in legacy_rows:
        source_native_id = evidence_id.split(":")[-1] if evidence_id else url
        canonical_evidence_id = build_canonical_evidence_id(platform, source_native_id)
        conn.execute(
            """
            INSERT INTO evidence (
                canonical_evidence_id, platform, source_native_id, channel, author_handle, url,
                content_raw, content_normalized, published_at, first_seen_at, last_seen_at,
                first_seen_run_id, last_seen_run_id, first_seen_report_date, last_seen_report_date,
                hit_count_total, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                canonical_evidence_id,
                platform,
                source_native_id,
                channel,
                None,
                url,
                content,
                content,
                report_date,
                report_date,
                report_date,
                None,
                None,
                report_date,
                report_date,
                1,
                payload_json,
            ),
        )
    conn.execute("DROP TABLE evidence_legacy")



def _migrate_legacy_signals(conn: sqlite3.Connection) -> None:
    columns = _table_columns(conn, "signals")
    if not columns or "signal_key" in columns:
        return
    legacy_rows = conn.execute(
        "SELECT signal_id, report_date, channel, title, payload_json FROM signals"
    ).fetchall()
    conn.execute("ALTER TABLE signals RENAME TO signals_legacy")
    _create_signal_tables(conn)
    for signal_id, report_date, channel, title, payload_json in legacy_rows:
        conn.execute(
            "INSERT OR REPLACE INTO daily_signal_snapshots (report_date, signal_key, channel, title, payload_json) VALUES (?, ?, ?, ?, ?)",
            (report_date, signal_id, channel, title, payload_json),
        )
        conn.execute(
            "INSERT OR REPLACE INTO signals (signal_key, latest_report_date, channel, title, payload_json) VALUES (?, ?, ?, ?, ?)",
            (signal_id, report_date, channel, title, payload_json),
        )
    conn.execute("DROP TABLE signals_legacy")


def init_db(db_path: str | Path) -> None:
    with _connect(db_path) as conn:
        _migrate_legacy_evidence(conn)
        _migrate_legacy_signals(conn)
        _create_evidence_table(conn)
        _create_signal_tables(conn)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS search_runs (
                run_id TEXT PRIMARY KEY,
                report_date TEXT NOT NULL,
                platform TEXT NOT NULL,
                channel TEXT NOT NULL,
                query_text TEXT NOT NULL,
                lookback_hours INTEGER NOT NULL,
                limit_count INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                raw_hit_count INTEGER NOT NULL DEFAULT 0,
                unique_hit_count INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS search_hits (
                hit_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                canonical_evidence_id TEXT NOT NULL,
                source_native_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                report_date TEXT NOT NULL,
                rank_in_response INTEGER NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_reports (
                report_date TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS weekly_reports (
                week_label TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL
            )
            """
        )


def _normalize_evidence_row(row: dict[str, Any]) -> dict[str, Any]:
    platform = row["platform"]
    source_native_id = row.get("source_native_id") or row.get("post_id")
    if not source_native_id:
        legacy_id = row.get("evidence_id")
        if legacy_id and ":" in legacy_id:
            source_native_id = legacy_id.split(":")[-1]
        else:
            source_native_id = legacy_id or row["url"]
    canonical_evidence_id = row.get("canonical_evidence_id") or build_canonical_evidence_id(platform, source_native_id)
    seen_at = row.get("seen_at") or row.get("last_seen_at") or row.get("first_seen_at") or row.get("report_date")
    report_date = row.get("report_date") or (seen_at[:10] if isinstance(seen_at, str) and len(seen_at) >= 10 else "unknown")
    return {
        "canonical_evidence_id": canonical_evidence_id,
        "platform": platform,
        "source_native_id": source_native_id,
        "channel": row["channel"],
        "author_handle": row.get("author_handle"),
        "url": row["url"],
        "content_raw": row.get("content_raw") or row.get("content") or "",
        "content_normalized": row.get("content_normalized") or row.get("content") or "",
        "published_at": row.get("published_at") or report_date,
        "seen_at": seen_at or report_date,
        "run_id": row.get("run_id"),
        "report_date": report_date,
        "payload_json": json.dumps(row, ensure_ascii=False),
    }


def insert_evidence(db_path: str | Path, evidence_rows: list[dict]) -> None:
    normalized_rows = [_normalize_evidence_row(row) for row in evidence_rows]
    with _connect(db_path) as conn:
        for row in normalized_rows:
            existing = conn.execute(
                "SELECT first_seen_at, first_seen_run_id, first_seen_report_date, hit_count_total FROM evidence WHERE canonical_evidence_id = ?",
                (row["canonical_evidence_id"],),
            ).fetchone()
            if existing is None:
                conn.execute(
                    """
                    INSERT INTO evidence (
                        canonical_evidence_id, platform, source_native_id, channel, author_handle, url,
                        content_raw, content_normalized, published_at, first_seen_at, last_seen_at,
                        first_seen_run_id, last_seen_run_id, first_seen_report_date, last_seen_report_date,
                        hit_count_total, payload_json
                    ) VALUES (
                        :canonical_evidence_id, :platform, :source_native_id, :channel, :author_handle, :url,
                        :content_raw, :content_normalized, :published_at, :seen_at, :seen_at,
                        :run_id, :run_id, :report_date, :report_date, 1, :payload_json
                    )
                    """,
                    row,
                )
            else:
                first_seen_at, first_seen_run_id, first_seen_report_date, hit_count_total = existing
                conn.execute(
                    """
                    UPDATE evidence
                    SET channel = :channel,
                        author_handle = :author_handle,
                        url = :url,
                        content_raw = :content_raw,
                        content_normalized = :content_normalized,
                        published_at = :published_at,
                        last_seen_at = :seen_at,
                        last_seen_run_id = :run_id,
                        last_seen_report_date = :report_date,
                        hit_count_total = :hit_count_total,
                        payload_json = :payload_json
                    WHERE canonical_evidence_id = :canonical_evidence_id
                    """,
                    {
                        **row,
                        "hit_count_total": hit_count_total + 1,
                        "first_seen_at": first_seen_at,
                        "first_seen_run_id": first_seen_run_id,
                        "first_seen_report_date": first_seen_report_date,
                    },
                )


def insert_search_runs(db_path: str | Path, run_rows: list[dict]) -> None:
    with _connect(db_path) as conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO search_runs (
                run_id, report_date, platform, channel, query_text, lookback_hours, limit_count,
                started_at, finished_at, raw_hit_count, unique_hit_count, status, payload_json
            ) VALUES (
                :run_id, :report_date, :platform, :channel, :query_text, :lookback_hours, :limit_count,
                :started_at, :finished_at, :raw_hit_count, :unique_hit_count, :status, :payload_json
            )
            """,
            [
                {
                    **row,
                    "payload_json": json.dumps(row, ensure_ascii=False),
                }
                for row in run_rows
            ],
        )


def insert_search_hits(db_path: str | Path, hit_rows: list[dict]) -> None:
    with _connect(db_path) as conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO search_hits (
                hit_id, run_id, canonical_evidence_id, source_native_id, platform, report_date, rank_in_response, payload_json
            ) VALUES (
                :hit_id, :run_id, :canonical_evidence_id, :source_native_id, :platform, :report_date, :rank_in_response, :payload_json
            )
            """,
            [
                {
                    **row,
                    "payload_json": json.dumps(row, ensure_ascii=False),
                }
                for row in hit_rows
            ],
        )


def insert_signals(db_path: str | Path, signal_rows: list[dict]) -> None:
    with _connect(db_path) as conn:
        for row in signal_rows:
            signal_key = row.get("signal_key") or row.get("signal_id")
            payload = row.get("payload", {})
            snapshot_payload = {
                "signal_id": signal_key,
                "signal_key": signal_key,
                "report_date": row["report_date"],
                "channel": row["channel"],
                "title": row["title"],
                "payload": payload,
            }
            conn.execute(
                """
                INSERT OR REPLACE INTO daily_signal_snapshots (report_date, signal_key, channel, title, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    row["report_date"],
                    signal_key,
                    row["channel"],
                    row["title"],
                    json.dumps(snapshot_payload, ensure_ascii=False),
                ),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO signals (signal_key, latest_report_date, channel, title, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    signal_key,
                    row["report_date"],
                    row["channel"],
                    row["title"],
                    json.dumps(snapshot_payload, ensure_ascii=False),
                ),
            )


def save_daily_report(db_path: str | Path, report: dict) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO daily_reports (report_date, payload_json) VALUES (?, ?)",
            (report["report_date"], json.dumps(report, ensure_ascii=False)),
        )


def save_weekly_report(db_path: str | Path, report: dict) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO weekly_reports (week_label, payload_json) VALUES (?, ?)",
            (report["week_label"], json.dumps(report, ensure_ascii=False)),
        )


def load_daily_reports_between(db_path: str | Path, start_date: str, end_date: str) -> list[dict]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT payload_json FROM daily_reports WHERE report_date BETWEEN ? AND ? ORDER BY report_date",
            (start_date, end_date),
        ).fetchall()
    return [json.loads(row[0]) for row in rows]


def load_signals_for_date(db_path: str | Path, report_date: str) -> list[dict]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT payload_json FROM daily_signal_snapshots WHERE report_date = ? ORDER BY signal_key",
            (report_date,),
        ).fetchall()
    return [json.loads(row[0]) for row in rows]
