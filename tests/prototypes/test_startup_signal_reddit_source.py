from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from reddit_source import build_reddit_plan, check_reddit_credentials  # type: ignore  # noqa: E402


def test_check_reddit_credentials_false_when_missing_env(monkeypatch) -> None:
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("REDDIT_USER_AGENT", raising=False)

    assert check_reddit_credentials() is False


def test_build_reddit_plan_generates_query_and_subreddit_targets() -> None:
    plan = build_reddit_plan(
        subreddits=["sales", "smallbusiness"],
        query="alternative to manual CRM updates",
        limit=50,
    )

    assert plan["query"] == "alternative to manual CRM updates"
    assert plan["subreddits"] == ["sales", "smallbusiness"]
    assert plan["limit"] == 50
    assert "sales+smallbusiness" in plan["search_path"]
