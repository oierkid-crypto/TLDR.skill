from __future__ import annotations

import asyncio
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from agent.auxiliary_client import async_call_llm, extract_content_or_reasoning
from tools.transcription_tools import _transcribe_local, transcribe_audio


class VideoTranscriptDigestError(RuntimeError):
    """Raised when the video transcript digest pipeline cannot complete."""


SUPPORTED_PLATFORMS = {
    "youtube": {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"},
    "douyin": {"douyin.com", "www.douyin.com", "v.douyin.com", "iesdouyin.com"},
    "xiaohongshu": {"xiaohongshu.com", "www.xiaohongshu.com", "xhslink.com", "www.xiaohongshu.cn"},
}

_YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


@dataclass
class TranscriptResult:
    source: str
    text: str
    language: str | None = None
    title: str | None = None
    segments: list[dict[str, Any]] | None = None
    downloaded_media_path: str | None = None
    provider: str | None = None
    raw_text: str | None = None


@dataclass
class DigestResult:
    url: str
    platform: str
    transcript: TranscriptResult
    summary: str
    reality_check: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_platform(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if not host:
        raise VideoTranscriptDigestError(f"无法识别链接域名：{url}")
    for platform, hosts in SUPPORTED_PLATFORMS.items():
        if host in hosts:
            return platform
    raise VideoTranscriptDigestError(
        "暂只支持小红书、抖音、YouTube 链接；当前链接域名不在支持列表内。"
    )


def _extract_youtube_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.netloc.lower() == "youtu.be":
        candidate = parsed.path.strip("/")
        return candidate if _YOUTUBE_ID_RE.match(candidate) else None
    query = parsed.query or ""
    for part in query.split("&"):
        if part.startswith("v="):
            candidate = part.split("=", 1)[1]
            return candidate if _YOUTUBE_ID_RE.match(candidate) else None
    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) >= 2 and path_parts[0] in {"shorts", "embed", "live"}:
        candidate = path_parts[1]
        return candidate if _YOUTUBE_ID_RE.match(candidate) else None
    return None


def _import_youtube_transcript_api():
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
        return YouTubeTranscriptApi
    except ImportError as exc:
        raise VideoTranscriptDigestError(
            "缺少 youtube-transcript-api 依赖，无法优先抓取 YouTube 官方字幕。"
        ) from exc


def fetch_youtube_transcript(url: str, languages: list[str] | None = None) -> TranscriptResult:
    video_id = _extract_youtube_video_id(url)
    if not video_id:
        raise VideoTranscriptDigestError(f"无法从链接中提取 YouTube video id：{url}")

    api_cls = _import_youtube_transcript_api()
    try:
        api = api_cls()
        fetched = api.fetch(video_id, languages=languages or ["zh-Hans", "zh-CN", "zh", "en"])
        transcript_items = [dict(item) for item in fetched]
    except Exception as exc:
        raise VideoTranscriptDigestError(f"YouTube 字幕抓取失败：{exc}") from exc

    text = "\n".join(item.get("text", "").strip() for item in transcript_items if item.get("text"))
    if not text.strip():
        raise VideoTranscriptDigestError("YouTube 返回了空字幕。")

    return TranscriptResult(
        source="youtube_transcript_api",
        text=text.strip(),
        raw_text=text.strip(),
        segments=transcript_items,
    )


def _import_yt_dlp():
    try:
        import yt_dlp  # type: ignore
        return yt_dlp
    except ImportError as exc:
        raise VideoTranscriptDigestError(
            "缺少 yt-dlp 依赖，无法下载视频做转录。"
        ) from exc


def _resolve_cookies_from_browser() -> tuple[str, str | None] | None:
    browser = (os.getenv("HERMES_YTDLP_COOKIES_FROM_BROWSER") or "").strip()
    if not browser:
        return None
    browser_home = (os.getenv("HERMES_YTDLP_BROWSER_HOME") or "").strip() or None
    return browser, browser_home


def _with_browser_cookie_options(options: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    cookies_from_browser = _resolve_cookies_from_browser()
    previous_home = None
    if cookies_from_browser:
        browser, browser_home = cookies_from_browser
        options["cookiesfrombrowser"] = (browser, None, None, None)
        if browser_home:
            previous_home = os.environ.get("HOME")
            os.environ["HOME"] = browser_home
    return options, previous_home


def _restore_home(previous_home: str | None) -> None:
    if previous_home is not None:
        os.environ["HOME"] = previous_home


def _json3_to_text(json3_path: str) -> str:
    payload = json.loads(Path(json3_path).read_text(encoding="utf-8"))
    chunks: list[str] = []
    for event in payload.get("events", []):
        segs = event.get("segs") or []
        text = "".join(seg.get("utf8", "") for seg in segs)
        if text:
            chunks.append(text)
    transcript = "".join(chunks)
    transcript = re.sub(r"\n{3,}", "\n\n", transcript)
    transcript = re.sub(r"[ \t]+", " ", transcript)
    return transcript.strip()


def fetch_youtube_subtitle_transcript(url: str, languages: list[str] | None = None) -> TranscriptResult:
    yt_dlp = _import_yt_dlp()
    video_id = _extract_youtube_video_id(url)
    if not video_id:
        raise VideoTranscriptDigestError(f"无法从链接中提取 YouTube video id：{url}")

    with tempfile.TemporaryDirectory(prefix="yt-subs-") as tmp_dir:
        outtmpl = str(Path(tmp_dir) / "%(id)s.%(ext)s")
        options: dict[str, Any] = {
            "skip_download": True,
            "writeautomaticsub": True,
            "writesubtitles": True,
            "subtitlesformat": "json3",
            "subtitleslangs": languages or ["zh-Hans", "zh-Hant", "zh", "en"],
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
            "ignore_no_formats_error": True,
            "restrictfilenames": True,
        }
        options, previous_home = _with_browser_cookie_options(options)
        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                info = downloader.extract_info(url, download=True)
        finally:
            _restore_home(previous_home)

        subtitles = sorted(Path(tmp_dir).glob(f"{video_id}*.json3"))
        if not subtitles:
            raise VideoTranscriptDigestError("YouTube 自动字幕下载失败。")

        transcript_text = _json3_to_text(str(subtitles[0]))
        if not transcript_text:
            raise VideoTranscriptDigestError("YouTube 自动字幕内容为空。")

        return TranscriptResult(
            source="yt_dlp_subtitles",
            text=transcript_text,
            raw_text=transcript_text,
            title=(info or {}).get("title"),
            downloaded_media_path=str(subtitles[0]),
        )


def _import_requests():
    try:
        import requests  # type: ignore
        return requests
    except ImportError as exc:
        raise VideoTranscriptDigestError("缺少 requests 依赖。") from exc


def _resolve_final_url(url: str) -> str:
    requests = _import_requests()
    response = requests.get(
        url,
        allow_redirects=True,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        },
    )
    response.raise_for_status()
    return response.url


def _import_playwright():
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
        return sync_playwright
    except ImportError as exc:
        raise VideoTranscriptDigestError("缺少 playwright 依赖，无法走浏览器回退抓取抖音。") from exc


def _default_chrome_executable() -> str:
    return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def fetch_douyin_via_browser(url: str, workspace: Path) -> dict[str, Any]:
    sync_playwright = _import_playwright()
    final_url = _resolve_final_url(url)
    browser_path = os.getenv("HERMES_VIDEO_DIGEST_CHROME_PATH") or _default_chrome_executable()
    workspace.mkdir(parents=True, exist_ok=True)
    audio_url: str | None = None
    title: str | None = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=browser_path)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
        )

        def on_response(response):
            nonlocal audio_url
            candidate = response.url
            if "media-audio" in candidate and "/video/tos/" in candidate:
                audio_url = candidate

        page.on("response", on_response)
        page.goto(final_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(12000)
        title = page.title().removesuffix(" - 抖音").strip() or None

        if not audio_url:
            browser.close()
            raise VideoTranscriptDigestError("抖音页面已打开，但未捕获到音轨 URL。")

        response = page.context.request.get(
            audio_url,
            headers={
                "Referer": page.url,
                "User-Agent": page.evaluate("navigator.userAgent"),
            },
            timeout=60000,
        )
        if response.status != 200:
            browser.close()
            raise VideoTranscriptDigestError(f"抖音音轨下载失败：HTTP {response.status}")

        destination = workspace / "source.m4a"
        destination.write_bytes(response.body())
        browser.close()

    return {
        "path": str(destination),
        "title": title,
        "extractor": "playwright_douyin",
        "final_url": final_url,
    }


def download_media(url: str, workspace: Path) -> dict[str, Any]:
    workspace.mkdir(parents=True, exist_ok=True)
    yt_dlp = _import_yt_dlp()
    output_template = str(workspace / "source.%(ext)s")
    options: dict[str, Any] = {
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "restrictfilenames": True,
        "format": "b[ext=mp4]/b[ext=webm]/b",
    }
    options, previous_home = _with_browser_cookie_options(options)

    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=True)
            file_path = Path(downloader.prepare_filename(info))
    finally:
        _restore_home(previous_home)

    if not file_path.exists():
        requested = info.get("requested_downloads") or []
        if requested:
            candidate = requested[0].get("filepath")
            if candidate:
                file_path = Path(candidate)
    if not file_path.exists():
        matches = sorted(workspace.glob("source.*"))
        if matches:
            file_path = matches[0]
    if not file_path.exists():
        raise VideoTranscriptDigestError("视频下载完成后未找到本地文件。")

    return {
        "path": str(file_path),
        "title": info.get("title"),
        "uploader": info.get("uploader"),
        "duration": info.get("duration"),
        "extractor": info.get("extractor_key") or info.get("extractor"),
    }


def download_media_for_platform(platform: str, url: str, workspace: Path) -> dict[str, Any]:
    if platform == "douyin":
        return fetch_douyin_via_browser(url, workspace)
    return download_media(url, workspace)


def transcribe_downloaded_media(media_path: str) -> TranscriptResult:
    result = transcribe_audio(media_path)
    if not result.get("success"):
        error = result.get("error") or "转录失败。"
        if "File too large" in error:
            local_result = _transcribe_local(media_path, "base")
            if local_result.get("success"):
                result = local_result
            else:
                raise VideoTranscriptDigestError(local_result.get("error") or error)
        else:
            raise VideoTranscriptDigestError(error)
    transcript = (result.get("transcript") or "").strip()
    if not transcript:
        raise VideoTranscriptDigestError("转录结果为空。")
    return TranscriptResult(
        source="audio_transcription",
        text=transcript,
        raw_text=transcript,
        provider=result.get("provider"),
        downloaded_media_path=media_path,
    )


async def _call_text_model(system_prompt: str, user_prompt: str, *, max_tokens: int = 1400) -> str:
    response = await async_call_llm(
        task="call",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=max_tokens,
    )
    text = extract_content_or_reasoning(response).strip()
    if not text:
        raise VideoTranscriptDigestError("LLM 返回空结果，无法继续处理。")
    return text


def _chunk_text(text: str, max_chars: int = 12000) -> list[str]:
    clean = text.strip()
    if len(clean) <= max_chars:
        return [clean]
    chunks: list[str] = []
    cursor = 0
    overlap = 800
    while cursor < len(clean):
        end = min(len(clean), cursor + max_chars)
        chunk = clean[cursor:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(clean):
            break
        cursor = max(0, end - overlap)
    return chunks


async def _optimize_transcript_async(transcript: TranscriptResult) -> TranscriptResult:
    system_prompt = (
        "你是专业视频转录编辑。你的任务不是总结，而是把原始转录稿整理成更适合人类阅读的稿子。"
        "必须忠于原意，不新增事实。优先修正常见 ASR 错词、英文术语、缩写、标点、断句和分段。"
    )
    user_prompt = (
        "请把下面的原始转录稿整理成高可读版本，要求：\n"
        "1. 保留原意，不做总结，不删关键观点。\n"
        "2. 修正明显 ASR 错字，尤其是中英混杂术语，如 token、AIDC、Agent 等。\n"
        "3. 补标点，合理分段，每段 2-5 句。\n"
        "4. 如果个别词拿不准，也要基于上下文做最合理修复。\n"
        "5. 输出仅包含整理后的转录稿正文。\n\n"
        f"标题：{transcript.title or 'Untitled'}\n"
        f"原始转录稿：\n{transcript.text}"
    )
    cleaned = await _call_text_model(system_prompt, user_prompt, max_tokens=2200)
    return TranscriptResult(
        source=transcript.source,
        text=cleaned.strip(),
        raw_text=transcript.raw_text or transcript.text,
        language=transcript.language,
        title=transcript.title,
        segments=transcript.segments,
        downloaded_media_path=transcript.downloaded_media_path,
        provider=transcript.provider,
    )


def optimize_transcript(transcript: TranscriptResult) -> TranscriptResult:
    return asyncio.run(_optimize_transcript_async(transcript))


async def summarize_and_reality_check(platform: str, url: str, transcript_text: str) -> tuple[str, str]:
    summary_system = (
        "你是严谨的视频内容分析助手。请基于已经整理好的转录稿，用中文输出高密度、层次分明的总结。"
    )
    reality_system = (
        "你是严谨的 Reality Check 编辑。请基于转录稿，判断哪些结论较稳、哪些地方可能夸张或证据不足。"
    )

    chunks = _chunk_text(transcript_text)
    if len(chunks) == 1:
        summary = await _call_text_model(
            summary_system,
            (
                f"平台：{platform}\n链接：{url}\n"
                "请输出一个层次清晰的总结，结构固定为：\n"
                "### 一句话结论\n"
                "### 核心要点\n- 3~6 条 bullet\n"
                "### 关键信号\n- 2~4 条 bullet\n\n"
                f"转录稿：\n{chunks[0]}"
            ),
        )
        reality_check = await _call_text_model(
            reality_system,
            (
                f"平台：{platform}\n链接：{url}\n"
                "请输出一个层次清晰的 Reality Check，结构固定为：\n"
                "### 核心判断\n"
                "### 哪些点相对可信\n- 2~5 条 bullet\n"
                "### 哪些点需要谨慎\n- 2~5 条 bullet\n"
                "### 最终结论\n"
                "不要输出‘内容结构与表达风格 / 亮点 / 适合谁看 / 可执行建议’。\n\n"
                f"转录稿：\n{chunks[0]}"
            ),
        )
        return summary, reality_check

    chunk_summaries: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        chunk_summary = await _call_text_model(
            summary_system,
            (
                f"平台：{platform}\n链接：{url}\n"
                f"这是第 {index}/{len(chunks)} 段转录。请用 4 条以内 bullet 总结这段信息。\n\n"
                f"转录稿：\n{chunk}"
            ),
        )
        chunk_summaries.append(f"[Chunk {index}]\n{chunk_summary}")

    stitched = "\n\n".join(chunk_summaries)
    summary = await _call_text_model(
        summary_system,
        (
            f"平台：{platform}\n链接：{url}\n"
            "请基于分段摘要输出最终总结，结构固定为：\n"
            "### 一句话结论\n"
            "### 核心要点\n- 3~6 条 bullet\n"
            "### 关键信号\n- 2~4 条 bullet\n\n"
            f"分段摘要：\n{stitched}"
        ),
    )
    reality_check = await _call_text_model(
        reality_system,
        (
            f"平台：{platform}\n链接：{url}\n"
            "请基于分段摘要输出最终 Reality Check，结构固定为：\n"
            "### 核心判断\n"
            "### 哪些点相对可信\n- 2~5 条 bullet\n"
            "### 哪些点需要谨慎\n- 2~5 条 bullet\n"
            "### 最终结论\n"
            "不要输出‘内容结构与表达风格 / 亮点 / 适合谁看 / 可执行建议’。\n\n"
            f"分段摘要：\n{stitched}"
        ),
    )
    return summary, reality_check


def process_video(url: str, *, prefer_youtube_captions: bool = True, languages: list[str] | None = None) -> DigestResult:
    platform = detect_platform(url)
    transcript: TranscriptResult | None = None

    if platform == "youtube" and prefer_youtube_captions:
        try:
            transcript = fetch_youtube_transcript(url, languages=languages)
        except VideoTranscriptDigestError:
            try:
                transcript = fetch_youtube_subtitle_transcript(url, languages=languages)
            except VideoTranscriptDigestError:
                transcript = None

    if transcript is None:
        with tempfile.TemporaryDirectory(prefix="video-digest-") as tmp_dir:
            download_meta = download_media_for_platform(platform, url, Path(tmp_dir))
            transcript = transcribe_downloaded_media(download_meta["path"])
            transcript.title = download_meta.get("title")

    transcript = optimize_transcript(transcript)
    summary, reality_check = asyncio.run(summarize_and_reality_check(platform, url, transcript.text))
    return DigestResult(
        url=url,
        platform=platform,
        transcript=transcript,
        summary=summary,
        reality_check=reality_check,
    )


def render_markdown_report(result: DigestResult) -> str:
    title_line = result.transcript.title or "Untitled"
    provider_line = result.transcript.provider or result.transcript.source
    return "\n".join(
        [
            f"# 视频转录 Digest - {title_line}",
            "",
            f"- 平台：{result.platform}",
            f"- 链接：{result.url}",
            f"- 转录来源：{provider_line}",
            "",
            "## 总结",
            result.summary.strip(),
            "",
            "## Reality Check",
            result.reality_check.strip(),
            "",
            "## 转录稿",
            result.transcript.text.strip(),
            "",
        ]
    ).strip() + "\n"


def render_json_report(result: DigestResult) -> str:
    return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
