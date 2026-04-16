from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from reddit_source import build_reddit_request_headers, preview_reddit_fetch_job  # type: ignore  # noqa: E402


def test_build_reddit_request_headers_uses_user_agent() -> None:
    headers = build_reddit_request_headers(user_agent="startup-signal-radar/0.1")

    assert headers["User-Agent"] == "startup-signal-radar/0.1"


def test_preview_reddit_fetch_job_emits_url_and_headers() -> None:
    preview = preview_reddit_fetch_job(
        subreddits=["sales", "SaaS"],
        query="alternative to manual CRM updates",
        user_agent="startup-signal-radar/0.1",
        limit=25,
    )

    assert "sales+SaaS" in preview["search_path"]
    assert preview["headers"]["User-Agent"] == "startup-signal-radar/0.1"
    assert preview["limit"] == 25
