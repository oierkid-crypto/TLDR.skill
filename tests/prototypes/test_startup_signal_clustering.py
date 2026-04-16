from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from cluster import cluster_signals, cluster_to_problem_cluster  # type: ignore  # noqa: E402
from extract import extract_signal  # type: ignore  # noqa: E402
from normalize import normalize_reddit_post, normalize_x_post, normalize_xiaohongshu_post  # type: ignore  # noqa: E402


def test_cluster_signals_groups_cross_platform_crm_update_pain() -> None:
    reddit_signal = extract_signal(
        normalize_reddit_post(
            {
                "id": "r1",
                "subreddit": "sales",
                "title": "Manually updating CRM after calls is exhausting",
                "selftext": "Looking for a tool that turns call notes into HubSpot updates.",
                "author": "rep1",
                "created_utc": 1713250200,
                "score": 33,
                "num_comments": 6,
                "permalink": "/r/sales/comments/r1/example/",
            }
        )
    )
    x_signal = extract_signal(
        normalize_x_post(
            {
                "id": "x1",
                "text": "I hate manually pushing sales call notes into CRM. Need a better tool for HubSpot follow-up.",
                "author_username": "ae_ops",
                "created_at": "2026-04-16T10:30:00Z",
                "public_metrics": {"like_count": 9, "reply_count": 2, "retweet_count": 1},
                "url": "https://x.com/ae_ops/status/x1",
            }
        )
    )
    xhs_signal = extract_signal(
        normalize_xiaohongshu_post(
            {
                "note_id": "xhs_crm_1",
                "title": "销售跟进录音整理太麻烦",
                "desc": "希望有工具把通话内容自动整理成 CRM 跟进，不想再手工录入。",
                "user_nickname": "销售运营",
                "time": "2026-04-16 10:40:00",
                "liked_count": 15,
                "comment_count": 4,
                "share_count": 1,
                "url": "https://www.xiaohongshu.com/explore/xhs_crm_1",
            }
        )
    )

    clusters = cluster_signals([reddit_signal, x_signal, xhs_signal])

    assert len(clusters) == 1
    assert len(clusters[0]) == 3


def test_cluster_to_problem_cluster_summarizes_founder_relevant_fields() -> None:
    reddit_signal = extract_signal(
        normalize_reddit_post(
            {
                "id": "r2",
                "subreddit": "sales",
                "title": "Need a tool that converts calls into CRM updates",
                "selftext": "I'd pay for a workflow that drafts follow-ups and updates HubSpot.",
                "author": "rep2",
                "created_utc": 1713250500,
                "score": 57,
                "num_comments": 11,
                "permalink": "/r/sales/comments/r2/example/",
            }
        )
    )
    x_signal = extract_signal(
        normalize_x_post(
            {
                "id": "x2",
                "text": "Looking for an alternative that turns meeting notes into CRM updates automatically.",
                "author_username": "sales_founder",
                "created_at": "2026-04-16T11:10:00Z",
                "public_metrics": {"like_count": 14, "reply_count": 1, "retweet_count": 0},
                "url": "https://x.com/sales_founder/status/x2",
            }
        )
    )

    cluster = cluster_to_problem_cluster([reddit_signal, x_signal], cluster_id="cluster_crm_1")

    assert cluster["cluster_id"] == "cluster_crm_1"
    assert cluster["workflow"]["name"] == "crm updates"
    assert cluster["signals"]["replacement_intent"] == 1.0
    assert cluster["verdict"]["priority"] in {"high", "medium"}
    assert len(cluster["evidence"]) == 2
