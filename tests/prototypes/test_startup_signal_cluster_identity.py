from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from cluster import cluster_identity_key, stable_cluster_id  # type: ignore  # noqa: E402
from extract import extract_signal  # type: ignore  # noqa: E402
from normalize import normalize_reddit_post, normalize_x_post  # type: ignore  # noqa: E402


def test_cluster_identity_key_is_stable_across_platforms_for_same_workflow() -> None:
    reddit_signal = extract_signal(
        normalize_reddit_post(
            {
                "id": "rid_same",
                "subreddit": "sales",
                "title": "Need a tool to update CRM after calls",
                "selftext": "Looking for a better workflow for HubSpot updates.",
                "author": "rep_same",
                "created_utc": 1713252000,
                "score": 5,
                "num_comments": 1,
                "permalink": "/r/sales/comments/rid_same/example/",
            }
        )
    )
    x_signal = extract_signal(
        normalize_x_post(
            {
                "id": "x_same",
                "text": "Alternative to manual CRM updates after sales calls?",
                "author_username": "seller_same",
                "created_at": "2026-04-16T12:00:00Z",
                "public_metrics": {"like_count": 2, "reply_count": 0, "retweet_count": 0},
                "url": "https://x.com/seller_same/status/x_same",
            }
        )
    )

    assert cluster_identity_key(reddit_signal) == cluster_identity_key(x_signal)
    assert stable_cluster_id([reddit_signal, x_signal]) == stable_cluster_id([x_signal, reddit_signal])


def test_stable_cluster_id_changes_when_ops_profile_changes() -> None:
    software_signal = extract_signal(
        normalize_reddit_post(
            {
                "id": "rid_soft",
                "subreddit": "sales",
                "title": "Need a tool to update CRM after calls",
                "selftext": "Looking for a better workflow for HubSpot updates.",
                "author": "rep_soft",
                "created_utc": 1713252100,
                "score": 5,
                "num_comments": 1,
                "permalink": "/r/sales/comments/rid_soft/example/",
            }
        )
    )
    ops_signal = extract_signal(
        normalize_x_post(
            {
                "id": "x_ops",
                "text": "线下活动组织太累，地推和办社群很重。",
                "author_username": "offline_ops",
                "created_at": "2026-04-16T12:10:00Z",
                "public_metrics": {"like_count": 2, "reply_count": 0, "retweet_count": 0},
                "url": "https://x.com/offline_ops/status/x_ops",
            }
        )
    )

    assert stable_cluster_id([software_signal]) != stable_cluster_id([ops_signal])
