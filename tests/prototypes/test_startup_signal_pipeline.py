from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from normalize import normalize_reddit_post, normalize_x_post, normalize_xiaohongshu_post  # type: ignore  # noqa: E402
from extract import extract_signal  # type: ignore  # noqa: E402
from reports import build_daily_report  # type: ignore  # noqa: E402
from opportunity import score_opportunity  # type: ignore  # noqa: E402


def test_normalize_reddit_post_maps_into_canonical_shape() -> None:
    raw = {
        "id": "abc123",
        "subreddit": "sales",
        "title": "Tired of manually updating CRM after every call",
        "selftext": "I wish there was a tool that turns call notes into HubSpot updates.",
        "author": "alice",
        "created_utc": 1713250000,
        "score": 42,
        "num_comments": 8,
        "permalink": "/r/sales/comments/abc123/example/",
    }

    post = normalize_reddit_post(raw)

    assert post.platform == "reddit"
    assert post.source_type == "subreddit_post"
    assert post.engagement.likes == 42
    assert "HubSpot" in post.raw_text


def test_extract_signal_marks_replacement_and_seo_intent() -> None:
    post = normalize_x_post(
        {
            "id": "tweet_1",
            "text": "Looking for an alternative to Gong. I hate manually turning call notes into CRM updates.",
            "author_username": "founder_ops",
            "created_at": "2026-04-16T10:00:00Z",
            "public_metrics": {"like_count": 12, "reply_count": 3, "retweet_count": 1},
            "url": "https://x.com/founder_ops/status/tweet_1",
        }
    )

    signal = extract_signal(post)

    assert signal.replacement_intent is True
    assert signal.seo_intent is True
    assert signal.heavy_ops_penalty is False
    assert signal.workflow == "crm updates"


def test_score_opportunity_rejects_offline_heavy_ops_case() -> None:
    post = normalize_xiaohongshu_post(
        {
            "note_id": "xhs_1",
            "title": "想做本地宝妈线下社群，但组织活动太累了",
            "desc": "线下活动、社群维护、地推都太重了，虽然需求很强。",
            "user_nickname": "mama_club",
            "time": "2026-04-16 11:00:00",
            "liked_count": 120,
            "comment_count": 25,
            "share_count": 5,
            "url": "https://www.xiaohongshu.com/explore/xhs_1",
        }
    )

    signal = extract_signal(post)
    scored = score_opportunity(signal)

    assert scored["decision"]["status"] == "reject"
    assert scored["founder_fit"]["ops_intensity"] == "high"


def test_build_daily_report_orders_by_overall_score() -> None:
    winning = score_opportunity(
        extract_signal(
            normalize_reddit_post(
                {
                    "id": "win_1",
                    "subreddit": "sales",
                    "title": "Need a tool that converts sales calls into CRM updates",
                    "selftext": "I'd pay for a tool that extracts follow-ups and updates HubSpot automatically.",
                    "author": "ae_1",
                    "created_utc": 1713250100,
                    "score": 65,
                    "num_comments": 12,
                    "permalink": "/r/sales/comments/win_1/example/",
                }
            )
        )
    )
    losing = score_opportunity(
        extract_signal(
            normalize_xiaohongshu_post(
                {
                    "note_id": "lose_1",
                    "title": "社区活动组织太累",
                    "desc": "要见很多人、办线下活动、社群维护很累。",
                    "user_nickname": "offline_ops",
                    "time": "2026-04-16 11:00:00",
                    "liked_count": 88,
                    "comment_count": 14,
                    "share_count": 2,
                    "url": "https://www.xiaohongshu.com/explore/lose_1",
                }
            )
        )
    )

    report = build_daily_report([losing, winning], report_date="2026-04-16")

    assert report["top_opportunities"][0]["title"] == winning["title"]
    assert report["top_opportunities"][0]["decision"]["status"] == "prototype_next"
