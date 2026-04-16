from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from channel_router import classify_channel_from_post, classify_channel_from_signal  # type: ignore  # noqa: E402
from extract import extract_signal  # type: ignore  # noqa: E402
from normalize import normalize_reddit_post, normalize_x_post  # type: ignore  # noqa: E402
from query_builder import load_taxonomy  # type: ignore  # noqa: E402


TAXONOMY_PATH = "prototypes/startup_signal_radar/config/query_taxonomy.example.yaml"


def test_classify_channel_from_signal_routes_sales_crm_to_2b() -> None:
    taxonomy = load_taxonomy(TAXONOMY_PATH)
    post = normalize_reddit_post(
        {
            "id": "crm_1",
            "subreddit": "sales",
            "title": "Need a tool to automate CRM updates after calls",
            "selftext": "Our sales team keeps manually updating HubSpot after every call.",
            "author": "ae_1",
            "created_utc": 1713250000,
            "score": 10,
            "num_comments": 2,
            "permalink": "/r/sales/comments/crm_1/example/",
        }
    )
    signal = extract_signal(post)

    assert classify_channel_from_signal(signal, taxonomy) == "2b"


def test_classify_channel_from_signal_routes_creator_workflow_to_2p() -> None:
    taxonomy = load_taxonomy(TAXONOMY_PATH)
    post = normalize_x_post(
        {
            "id": "creator_1",
            "text": "As a creator and freelancer I need a better tool to organize client notes and exports.",
            "author_username": "creator_ops",
            "created_at": "2026-04-16T10:00:00Z",
            "public_metrics": {"like_count": 12, "reply_count": 3, "retweet_count": 1},
            "url": "https://x.com/creator_ops/status/creator_1",
        }
    )
    signal = extract_signal(post)

    assert classify_channel_from_signal(signal, taxonomy) == "2p"


def test_classify_channel_from_post_routes_consumer_shopper_pain_to_2c() -> None:
    taxonomy = load_taxonomy(TAXONOMY_PATH)
    post = normalize_x_post(
        {
            "id": "consumer_1",
            "text": "As a shopper I keep buying skincare tools that are annoying and not worth it.",
            "author_username": "shopper",
            "created_at": "2026-04-16T11:00:00Z",
            "public_metrics": {"like_count": 5, "reply_count": 1, "retweet_count": 0},
            "url": "https://x.com/shopper/status/consumer_1",
        }
    )

    assert classify_channel_from_post(post, taxonomy) == "2c"


def test_classify_channel_from_post_returns_none_for_unclassified_case() -> None:
    taxonomy = load_taxonomy(TAXONOMY_PATH)
    post = normalize_x_post(
        {
            "id": "misc_1",
            "text": "Today was sunny and I took a walk in the park.",
            "author_username": "misc_user",
            "created_at": "2026-04-16T12:00:00Z",
            "public_metrics": {"like_count": 1, "reply_count": 0, "retweet_count": 0},
            "url": "https://x.com/misc_user/status/misc_1",
        }
    )

    assert classify_channel_from_post(post, taxonomy) is None
