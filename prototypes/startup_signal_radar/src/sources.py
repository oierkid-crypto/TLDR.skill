from __future__ import annotations

import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _fixture_path(platform: str) -> Path:
    mapping = {
        "reddit": FIXTURE_DIR / "reddit_sample.json",
        "x": FIXTURE_DIR / "x_sample.json",
        "xiaohongshu": FIXTURE_DIR / "xiaohongshu_sample.json",
    }
    if platform not in mapping:
        raise KeyError(f"unknown platform: {platform}")
    return mapping[platform]


def load_fixture_source(platform: str) -> list[dict]:
    path = _fixture_path(platform)
    payload = json.loads(path.read_text())
    return [{"platform": platform, "raw": record} for record in payload]


def source_registry() -> dict[str, callable]:
    return {
        "reddit": lambda: load_fixture_source("reddit"),
        "x": lambda: load_fixture_source("x"),
        "xiaohongshu": lambda: load_fixture_source("xiaohongshu"),
    }
