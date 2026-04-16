from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from tldr_skill import video_digest
from tldr_skill.video_digest import DigestResult, TranscriptResult, VideoTranscriptDigestError


class _FakeResponse:
    def __init__(self, text: str):
        self.choices = [SimpleNamespace(message=SimpleNamespace(content=text))]


def test_detect_platform_supports_three_platforms() -> None:
    assert video_digest.detect_platform("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "youtube"
    assert video_digest.detect_platform("https://www.douyin.com/video/123") == "douyin"
    assert video_digest.detect_platform("https://www.xiaohongshu.com/explore/123") == "xiaohongshu"


def test_render_json_report_contains_transcript() -> None:
    result = DigestResult(
        url="https://example.com/video",
        platform="youtube",
        transcript=TranscriptResult(source="youtube_transcript_api", text="优化稿", raw_text="原始稿", title="demo"),
        summary="总结",
        reality_check="核查",
    )
    payload = json.loads(video_digest.render_json_report(result))
    assert payload["summary"] == "总结"
    assert payload["transcript"]["text"] == "优化稿"
    assert payload["transcript"]["raw_text"] == "原始稿"


def test_render_markdown_report_uses_summary_and_reality_check_sections() -> None:
    result = DigestResult(
        url="https://example.com/video",
        platform="youtube",
        transcript=TranscriptResult(source="youtube_transcript_api", text="这是优化后的转录稿。", raw_text="这是原始转录稿", title="demo"),
        summary="### 核心结论\n- 要点 A",
        reality_check="### 哪些点可信\n- 点 1",
    )
    rendered = video_digest.render_markdown_report(result)
    assert "## 总结" in rendered
    assert "## Reality Check" in rendered
    assert "内容结构与表达风格" not in rendered
    assert "适合谁看" not in rendered
    assert "## 转录稿" in rendered
    assert "这是优化后的转录稿。" in rendered


def test_json3_to_text_extracts_plain_transcript(tmp_path: Path) -> None:
    sample = {"events": [{"segs": [{"utf8": "hello"}, {"utf8": " world"}]}, {"segs": [{"utf8": "\n"}]}, {"segs": [{"utf8": "again"}]}]}
    path = tmp_path / "sample.json3"
    path.write_text(json.dumps(sample), encoding="utf-8")
    assert video_digest._json3_to_text(str(path)) == "hello world\nagain"


def test_process_video_optimizes_transcript_before_summary() -> None:
    optimized = TranscriptResult(source="optimized", text="这是优化后的转录稿。", raw_text="偷肯 AIDC 没标点", title="标题")
    with patch.object(video_digest, "fetch_youtube_transcript", return_value=TranscriptResult(source="youtube_transcript_api", text="偷肯 AIDC 没标点", title="标题")), \
         patch.object(video_digest, "optimize_transcript", return_value=optimized) as mock_optimize, \
         patch.object(video_digest, "summarize_and_reality_check", return_value=("总结输出", "核查输出")) as mock_summary, \
         patch.object(video_digest, "download_media_for_platform") as mock_download:
        result = video_digest.process_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    mock_optimize.assert_called_once()
    mock_summary.assert_called_once_with("youtube", "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "这是优化后的转录稿。")
    mock_download.assert_not_called()
    assert result.transcript.text == "这是优化后的转录稿。"


def test_optimize_transcript_keeps_raw_text_and_returns_clean_version() -> None:
    async def fake_call_llm(*, task=None, messages=None, temperature=None, max_tokens=None, **_: object):
        assert task == "call"
        assert "AIDC" in messages[1]["content"]
        return _FakeResponse("第一段。\n\n第二段，带标点。")

    transcript = TranscriptResult(source="local", text="AIDC token 没标点", title="标题")
    with patch.object(video_digest, "async_call_llm", side_effect=fake_call_llm), \
         patch.object(video_digest, "extract_content_or_reasoning", side_effect=lambda response: response.choices[0].message.content):
        optimized = video_digest.optimize_transcript(transcript)

    assert optimized.raw_text == "AIDC token 没标点"
    assert optimized.text == "第一段。\n\n第二段，带标点。"


def test_process_video_falls_back_to_ytdlp_subtitles_then_asr() -> None:
    optimized = TranscriptResult(source="optimized", text="优化字幕", raw_text="字幕回退", title="标题")
    with patch.object(video_digest, "fetch_youtube_transcript", side_effect=VideoTranscriptDigestError("no captions")), \
         patch.object(video_digest, "fetch_youtube_subtitle_transcript", return_value=TranscriptResult(source="yt_dlp_subtitles", text="字幕回退", title="标题")) as mock_subs, \
         patch.object(video_digest, "optimize_transcript", return_value=optimized), \
         patch.object(video_digest, "summarize_and_reality_check", return_value=("总结", "核查")), \
         patch.object(video_digest, "download_media_for_platform") as mock_download:
        result = video_digest.process_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert result.transcript.text == "优化字幕"
    mock_subs.assert_called_once()
    mock_download.assert_not_called()


def test_process_video_falls_back_to_download_and_asr() -> None:
    optimized = TranscriptResult(source="optimized", text="优化 ASR", raw_text="ASR内容", title="下载标题")
    with patch.object(video_digest, "fetch_youtube_transcript", side_effect=VideoTranscriptDigestError("no captions")), \
         patch.object(video_digest, "fetch_youtube_subtitle_transcript", side_effect=VideoTranscriptDigestError("no subs")), \
         patch.object(video_digest, "download_media_for_platform", return_value={"path": "/tmp/a.mp4", "title": "下载标题"}), \
         patch.object(video_digest, "transcribe_downloaded_media", return_value=TranscriptResult(source="audio_transcription", text="ASR内容")), \
         patch.object(video_digest, "optimize_transcript", return_value=optimized), \
         patch.object(video_digest, "summarize_and_reality_check", return_value=("总结", "核查")):
        result = video_digest.process_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert result.transcript.text == "优化 ASR"
    assert result.transcript.title == "下载标题"


def test_transcribe_downloaded_media_falls_back_to_local_when_file_too_large() -> None:
    with patch.object(video_digest, "transcribe_audio", return_value={"success": False, "error": "File too large: 177.7MB (max 25MB)"}), \
         patch.object(video_digest, "_transcribe_local", return_value={"success": True, "provider": "local", "transcript": "本地转录"}):
        result = video_digest.transcribe_downloaded_media("/tmp/demo.mp4")

    assert result.provider == "local"
    assert result.text == "本地转录"


def test_resolve_cookies_from_browser_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HERMES_YTDLP_COOKIES_FROM_BROWSER", "chrome")
    monkeypatch.setenv("HERMES_YTDLP_BROWSER_HOME", "/Users/demo")
    assert video_digest._resolve_cookies_from_browser() == ("chrome", "/Users/demo")


def test_download_media_for_platform_uses_douyin_browser_fallback() -> None:
    with patch.object(video_digest, "fetch_douyin_via_browser", return_value={"path": "/tmp/a.m4a"}) as mock_fetch, \
         patch.object(video_digest, "download_media") as mock_download:
        result = video_digest.download_media_for_platform("douyin", "https://v.douyin.com/abc", Path("/tmp"))

    assert result["path"] == "/tmp/a.m4a"
    mock_fetch.assert_called_once()
    mock_download.assert_not_called()


@pytest.mark.asyncio
async def test_summarize_and_reality_check_single_chunk() -> None:
    calls: list[str] = []

    async def fake_call_llm(*, task=None, messages=None, temperature=None, max_tokens=None, **_: object):
        assert task == "call"
        calls.append(messages[1]["content"])
        return _FakeResponse("输出结果")

    with patch.object(video_digest, "async_call_llm", side_effect=fake_call_llm), \
         patch.object(video_digest, "extract_content_or_reasoning", side_effect=lambda response: response.choices[0].message.content):
        summary, reality_check = await video_digest.summarize_and_reality_check("youtube", "https://example.com", "短转录")

    assert summary == "输出结果"
    assert reality_check == "输出结果"
    assert len(calls) == 2


def test_cli_writes_markdown_file(tmp_path: Path) -> None:
    output_path = tmp_path / "digest.md"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT)

    script = (
        "import importlib.util; "
        f"spec=importlib.util.spec_from_file_location('tldr_skill_cli', r'{SRC_ROOT / 'tldr_skill' / 'cli.py'}'); "
        "mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); "
        "from tldr_skill.video_digest import DigestResult, TranscriptResult; "
        "mod.process_video = lambda *args, **kwargs: DigestResult(url='https://example.com', platform='youtube', transcript=TranscriptResult(source='youtube_transcript_api', text='稿子', raw_text='原稿', title='标题'), summary='总结', reality_check='核查'); "
        f"raise SystemExit(mod.main(['https://example.com', '--output', r'{output_path}']))"
    )
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=env, cwd=str(ROOT), check=False)

    assert result.returncode == 0
    rendered = output_path.read_text(encoding="utf-8")
    assert "## 总结" in rendered
    assert "## Reality Check" in rendered
    assert "稿子" in rendered
