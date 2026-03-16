"""Thin async wrapper around OpenRouter via the openai SDK."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from openai import AsyncOpenAI

from config import get_settings

logger = logging.getLogger(__name__)


def _build_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
    )


_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = _build_client()
    return _client


def _data_url(b64: str, mime: str = "image/jpeg") -> str:
    return f"data:{mime};base64,{b64}"


async def chat(
    prompt: str,
    *,
    system: str = "",
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    """Plain text chat completion (no images)."""
    settings = get_settings()
    model = model or settings.text_model
    messages: list[dict[str, Any]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    logger.info("LLM call  → model=%s  type=text  prompt_len=%d", model, len(prompt))
    t0 = time.perf_counter()

    resp = await get_client().chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    elapsed = time.perf_counter() - t0
    content = resp.choices[0].message.content or ""
    usage = resp.usage
    logger.info(
        "LLM done  ← model=%s  %.1fs  tokens=%s  response_len=%d",
        model,
        elapsed,
        f"{usage.prompt_tokens}→{usage.completion_tokens}" if usage else "?",
        len(content),
    )
    return content


async def chat_with_images(
    prompt: str,
    images: list[tuple[str, str]],  # list of (base64, mime_type)
    *,
    system: str = "",
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    """Vision chat completion with one or more images."""
    settings = get_settings()
    model = model or settings.vision_model

    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for b64, mime in images:
        content.append({
            "type": "image_url",
            "image_url": {"url": _data_url(b64, mime)},
        })

    messages: list[dict[str, Any]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": content})

    total_img_kb = sum(len(b64) * 3 // 4 // 1024 for b64, _ in images)
    logger.info(
        "LLM call  → model=%s  type=vision  images=%d  img_size=%dKB",
        model, len(images), total_img_kb,
    )
    t0 = time.perf_counter()

    resp = await get_client().chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    elapsed = time.perf_counter() - t0
    text = resp.choices[0].message.content or ""
    usage = resp.usage
    logger.info(
        "LLM done  ← model=%s  %.1fs  tokens=%s  response_len=%d",
        model,
        elapsed,
        f"{usage.prompt_tokens}→{usage.completion_tokens}" if usage else "?",
        len(text),
    )
    return text


async def chat_json(
    prompt: str,
    *,
    system: str = "",
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 8192,
) -> Any:
    """Chat completion that expects a JSON response. Parses and returns it."""
    raw = await chat(
        prompt,
        system=system,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]  # drop ```json
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("JSON parse failed: %s\nRaw response:\n%s", e, raw[:500])
        raise


async def chat_json_with_images(
    prompt: str,
    images: list[tuple[str, str]],
    *,
    system: str = "",
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 8192,
) -> Any:
    """Vision chat that expects a JSON response."""
    raw = await chat_with_images(
        prompt,
        images,
        system=system,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("JSON parse failed: %s\nRaw response:\n%s", e, raw[:500])
        raise
