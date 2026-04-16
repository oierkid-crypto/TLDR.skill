from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prototypes" / "startup_signal_radar" / "src"
sys.path.insert(0, str(ROOT))

from sources import load_fixture_source, source_registry  # type: ignore  # noqa: E402


def test_source_registry_exposes_expected_fixture_collectors() -> None:
    registry = source_registry()

    assert set(registry) >= {"reddit", "x", "xiaohongshu"}


def test_load_fixture_source_returns_platform_records() -> None:
    records = load_fixture_source("reddit")

    assert len(records) >= 1
    assert records[0]["platform"] == "reddit"
    assert "raw" in records[0]


def test_fixture_file_roundtrip_is_valid_json() -> None:
    fixture_path = Path("prototypes/startup_signal_radar/fixtures/reddit_sample.json")
    payload = json.loads(fixture_path.read_text())

    assert isinstance(payload, list)
    assert payload[0]["id"]
