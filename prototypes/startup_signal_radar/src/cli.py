from __future__ import annotations

import argparse

from db import init_db
from daily_radar import run_daily_radar
from report_writer import render_daily_user_needs_report, render_weekly_user_needs_report
from weekly_radar import run_weekly_radar


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="startup-signal-radar")
    subparsers = parser.add_subparsers(dest="command", required=True)

    daily = subparsers.add_parser("daily")
    daily.add_argument("--date", required=True)
    daily.add_argument("--db", required=True)
    daily.add_argument("--taxonomy", required=True)

    weekly = subparsers.add_parser("weekly")
    weekly.add_argument("--week-label", required=True)
    weekly.add_argument("--start-date", required=True)
    weekly.add_argument("--end-date", required=True)
    weekly.add_argument("--db", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    init_db(args.db)

    if args.command == "daily":
        report = run_daily_radar(
            report_date=args.date,
            db_path=args.db,
            taxonomy_path=args.taxonomy,
            platforms=["reddit", "x"],
        )
        print(render_daily_user_needs_report(report))
        return 0

    if args.command == "weekly":
        report = run_weekly_radar(
            week_label=args.week_label,
            start_date=args.start_date,
            end_date=args.end_date,
            db_path=args.db,
        )
        print(render_weekly_user_needs_report(report))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
