from __future__ import annotations

import asyncio
import os
from typing import Any

from openai import OpenAI

DEFAULT_MODEL = os.getenv("TLDR_SKILL_MODEL", os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
DEFAULT_BASE_URL = os.getenv("TLDR_SKILL_BASE_URL", os.getenv("OPENAI_BASE_URL"))


class LLMConfigError(RuntimeError):
    pass


def _resolve_client() -> tuple[OpenAI, str]:
    api_key = (
        os.getenv("TLDR_SKILL_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
    )
    if not api_key:
        raise LLMConfigError(
            "No LLM API key found. Set TLDR_SKILL_API_KEY, OPENAI_API_KEY, or OPENROUTER_API_KEY."
        )

    base_url = DEFAULT_BASE_URL
    if not base_url and os.getenv("OPENROUTER_API_KEY"):
        base_url = "https://openrouter.ai/api/v1"

    kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    client = OpenAI(**kwargs)
    model = os.getenv("TLDR_SKILL_MODEL", DEFAULT_MODEL)
    return client, model


async def async_call_llm(*, task: str | None = None, messages: list[dict[str, Any]], temperature: float = 0.2, max_tokens: int = 1400, model: str | None = None, **_: Any):
    if task not in (None, "call"):
        raise ValueError(f"Unsupported task: {task}")

    client, default_model = _resolve_client()
    chosen_model = model or default_model

    def _call():
        return client.chat.completions.create(
            model=chosen_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    return await asyncio.to_thread(_call)


def extract_content_or_reasoning(response: Any) -> str:
    if not getattr(response, "choices", None):
        return ""
    message = response.choices[0].message
    content = getattr(message, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "\n".join(part for part in parts if part).strip()
    return ""
