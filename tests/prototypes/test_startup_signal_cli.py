from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "prototypes" / "startup_signal_radar" / "src"


def test_cli_daily_and_weekly_commands_render_reports(tmp_path: Path) -> None:
    db_path = tmp_path / "radar.db"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT)

    daily = subprocess.run(
        [
            sys.executable,
            str(SRC_ROOT / "cli.py"),
            "daily",
            "--date",
            "2026-04-16",
            "--db",
            str(db_path),
            "--taxonomy",
            str(ROOT / "prototypes" / "startup_signal_radar" / "config" / "query_taxonomy.example.yaml"),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert daily.returncode == 0
    assert "2B" in daily.stdout

    weekly = subprocess.run(
        [
            sys.executable,
            str(SRC_ROOT / "cli.py"),
            "weekly",
            "--week-label",
            "2026-W16",
            "--start-date",
            "2026-04-14",
            "--end-date",
            "2026-04-20",
            "--db",
            str(db_path),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert weekly.returncode == 0
    assert "2B" in weekly.stdout


def test_daily_rerun_is_report_replace_but_evidence_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "radar.db"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT)
    args = [
        sys.executable,
        str(SRC_ROOT / "cli.py"),
        "daily",
        "--date",
        "2026-04-16",
        "--db",
        str(db_path),
        "--taxonomy",
        str(ROOT / "prototypes" / "startup_signal_radar" / "config" / "query_taxonomy.example.yaml"),
    ]

    first = subprocess.run(args, capture_output=True, text=True, env=env, check=False)
    second = subprocess.run(args, capture_output=True, text=True, env=env, check=False)

    assert first.returncode == 0
    assert second.returncode == 0

    with sqlite3.connect(db_path) as conn:
        evidence_count = conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
        report_count = conn.execute("SELECT COUNT(*) FROM daily_reports").fetchone()[0]
        run_count = conn.execute("SELECT COUNT(*) FROM search_runs").fetchone()[0]

    assert evidence_count > 0
    assert report_count == 1
    assert run_count >= 2
