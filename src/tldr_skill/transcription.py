from __future__ import annotations

import os
from pathlib import Path
from typing import Any

MAX_FILE_SIZE = 25 * 1024 * 1024


def _transcribe_local(media_path: str, model_name: str = "base", language: str | None = None) -> dict[str, Any]:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError:
        return {
            "success": False,
            "provider": "local",
            "error": "faster-whisper is not installed. Install with `pip install -e .[video]`.",
        }

    try:
        model = WhisperModel(model_name, device="auto", compute_type="int8")
        segments, info = model.transcribe(media_path, language=language)
        text = " ".join(segment.text.strip() for segment in segments if segment.text).strip()
        return {
            "success": bool(text),
            "provider": "local",
            "language": getattr(info, "language", None),
            "transcript": text,
            "error": "" if text else "Empty transcript.",
        }
    except Exception as exc:  # pragma: no cover - external runtime path
        return {"success": False, "provider": "local", "error": str(exc)}


def _transcribe_openai(media_path: str) -> dict[str, Any]:
    from openai import OpenAI

    api_key = os.getenv("TLDR_SKILL_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"success": False, "provider": "openai", "error": "OPENAI_API_KEY not set."}

    base_url = os.getenv("TLDR_SKILL_BASE_URL") or os.getenv("OPENAI_BASE_URL")
    kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    client = OpenAI(**kwargs)
    model = os.getenv("TLDR_SKILL_STT_MODEL", "whisper-1")

    with open(media_path, "rb") as fh:
        result = client.audio.transcriptions.create(model=model, file=fh)
    text = getattr(result, "text", "") or ""
    return {
        "success": bool(text.strip()),
        "provider": "openai",
        "transcript": text.strip(),
        "error": "" if text.strip() else "Empty transcript.",
    }


def transcribe_audio(media_path: str) -> dict[str, Any]:
    file_path = Path(media_path)
    if not file_path.exists():
        return {"success": False, "error": f"File not found: {media_path}"}

    if file_path.stat().st_size > MAX_FILE_SIZE:
        return {
            "success": False,
            "provider": "auto",
            "error": f"File too large: {file_path.stat().st_size / (1024 * 1024):.1f}MB (max 25MB)",
        }

    local = _transcribe_local(media_path)
    if local.get("success"):
        return local

    return _transcribe_openai(media_path)
