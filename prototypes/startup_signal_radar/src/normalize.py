from __future__ import annotations

from models import EngagementMetrics, NormalizedPost


REDDIT_BASE = "https://www.reddit.com"


def normalize_reddit_post(raw: dict) -> NormalizedPost:
    title = raw.get("title") or ""
    body = raw.get("selftext") or ""
    return NormalizedPost(
        post_id=str(raw.get("id", "")),
        platform="reddit",
        source_type="subreddit_post",
        url=f"{REDDIT_BASE}{raw.get('permalink', '')}",
        created_at=str(raw.get("created_utc", "")),
        author_handle=raw.get("author"),
        raw_text=f"{title}\n\n{body}".strip(),
        title=title or None,
        language="en",
        community=raw.get("subreddit"),
        engagement=EngagementMetrics(
            likes=int(raw.get("score", 0) or 0),
            comments=int(raw.get("num_comments", 0) or 0),
            shares=0,
        ),
        metadata={"raw": raw},
    )


def normalize_x_post(raw: dict) -> NormalizedPost:
    metrics = raw.get("public_metrics", {})
    return NormalizedPost(
        post_id=str(raw.get("id", "")),
        platform="x",
        source_type="tweet",
        url=raw.get("url", ""),
        created_at=str(raw.get("created_at", "")),
        author_handle=raw.get("author_username"),
        raw_text=(raw.get("text") or "").strip(),
        title=None,
        language="en",
        engagement=EngagementMetrics(
            likes=int(metrics.get("like_count", 0) or 0),
            comments=int(metrics.get("reply_count", 0) or 0),
            shares=int(metrics.get("retweet_count", 0) or 0),
        ),
        metadata={"raw": raw},
    )


def normalize_xiaohongshu_post(raw: dict) -> NormalizedPost:
    title = raw.get("title") or ""
    body = raw.get("desc") or ""
    return NormalizedPost(
        post_id=str(raw.get("note_id", "")),
        platform="xiaohongshu",
        source_type="note",
        url=raw.get("url", ""),
        created_at=str(raw.get("time", "")),
        author_handle=raw.get("user_nickname"),
        raw_text=f"{title}\n\n{body}".strip(),
        title=title or None,
        language="zh",
        engagement=EngagementMetrics(
            likes=int(raw.get("liked_count", 0) or 0),
            comments=int(raw.get("comment_count", 0) or 0),
            shares=int(raw.get("share_count", 0) or 0),
        ),
        metadata={"raw": raw},
    )
