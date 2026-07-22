"""
LLM client wrapper.

Supports two providers:
  1. Anthropic (direct) — when ANTHROPIC_API_KEY starts with "sk-ant-"
  2. OpenRouter — when ANTHROPIC_API_KEY starts with "sk-or-"

Kept behind a single async-generator function so swapping providers later
doesn't require touching the route or prompt-building code — only this module.
"""

import json
from collections.abc import AsyncGenerator

import httpx

from app.config import get_settings
from app.core.errors import AIProviderError
from app.core.logging import get_logger
from app.ai.prompts import SYSTEM_PROMPT

logger = get_logger(__name__)

_ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
_OPENROUTER_MODEL = "openai/gpt-4o-mini"
_MAX_TOKENS = 1024
_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _is_openrouter() -> bool:
    return get_settings().anthropic_api_key.startswith("sk-or-")


# ---------------------------------------------------------------------------
# OpenRouter helpers (OpenAI-compatible API)
# ---------------------------------------------------------------------------

async def _openrouter_stream(messages: list[dict], system_prompt: str) -> AsyncGenerator[str, None]:
    """Stream a chat response via OpenRouter's OpenAI-compatible API."""
    settings = get_settings()

    openai_messages = [{"role": "system", "content": system_prompt}]
    for m in messages:
        openai_messages.append({"role": m["role"], "content": m["content"]})

    headers = {
        "Authorization": f"Bearer {settings.anthropic_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "EcoMind AI",
    }

    payload = {
        "model": _OPENROUTER_MODEL,
        "messages": openai_messages,
        "max_tokens": _MAX_TOKENS,
        "stream": True,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{_OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    error_text = body.decode()
                    logger.error("OpenRouter error %s: %s", response.status_code, error_text)
                    raise AIProviderError(f"OpenRouter error ({response.status_code}): {error_text[:200]}")

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        text = delta.get("content", "")
                        if text:
                            yield text
                    except (json.JSONDecodeError, IndexError, KeyError):
                        continue
    except AIProviderError:
        raise
    except Exception as exc:
        logger.error("OpenRouter error: %s", exc)
        raise AIProviderError(f"OpenRouter connection error: {exc}") from exc


async def _openrouter_completion(system_prompt: str, user_message: str, max_tokens: int = 800) -> str:
    """Single-shot completion via OpenRouter."""
    settings = get_settings()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    headers = {
        "Authorization": f"Bearer {settings.anthropic_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "EcoMind AI",
    }

    payload = {
        "model": _OPENROUTER_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{_OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            if resp.status_code != 200:
                logger.error("OpenRouter error %s: %s", resp.status_code, resp.text)
                raise AIProviderError(f"OpenRouter error ({resp.status_code}): {resp.text[:200]}")

            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except httpx.HTTPError as exc:
        logger.error("OpenRouter HTTP error: %s", exc)
        raise AIProviderError("The AI service failed to respond. Please try again.") from exc


# ---------------------------------------------------------------------------
# Anthropic (direct) helpers
# ---------------------------------------------------------------------------

async def _anthropic_stream(messages: list[dict]) -> AsyncGenerator[str, None]:
    """Stream a chat response via Anthropic's native API."""
    settings = get_settings()

    try:
        import anthropic
    except ImportError as exc:
        raise AIProviderError("AI provider SDK is not installed on the server.") from exc

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    try:
        async with client.messages.stream(
            model=_ANTHROPIC_MODEL,
            max_tokens=_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except anthropic.APIError as exc:
        logger.error("Anthropic API error during chat stream: %s", exc)
        raise AIProviderError("The AI service failed to respond. Please try again.") from exc


async def _anthropic_completion(system_prompt: str, user_message: str, max_tokens: int = 800) -> str:
    """Single-shot completion via Anthropic's native API."""
    settings = get_settings()

    try:
        import anthropic
    except ImportError as exc:
        raise AIProviderError("AI provider SDK is not installed on the server.") from exc

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    try:
        response = await client.messages.create(
            model=_ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text
    except anthropic.APIError as exc:
        logger.error("Anthropic API error during completion: %s", exc)
        raise AIProviderError("The AI service failed to respond. Please try again.") from exc


# ---------------------------------------------------------------------------
# Public interface (unchanged signatures)
# ---------------------------------------------------------------------------

async def stream_chat_response(messages: list[dict]) -> AsyncGenerator[str, None]:
    """
    Streams the AI's reply as a sequence of text chunks.
    Automatically routes to OpenRouter or Anthropic based on the API key prefix.
    """
    settings = get_settings()

    if not settings.anthropic_api_key:
        raise AIProviderError(
            "AI chat is not configured yet — ANTHROPIC_API_KEY is missing on the server."
        )

    if _is_openrouter():
        async for chunk in _openrouter_stream(messages, SYSTEM_PROMPT):
            yield chunk
    else:
        async for chunk in _anthropic_stream(messages):
            yield chunk


async def generate_completion(system_prompt: str, user_message: str, max_tokens: int = 800) -> str:
    """
    Single-shot (non-streaming) completion.
    Automatically routes to OpenRouter or Anthropic based on the API key prefix.
    """
    settings = get_settings()

    if not settings.anthropic_api_key:
        raise AIProviderError(
            "AI features are not configured yet — ANTHROPIC_API_KEY is missing on the server."
        )

    if _is_openrouter():
        return await _openrouter_completion(system_prompt, user_message, max_tokens)
    else:
        return await _anthropic_completion(system_prompt, user_message, max_tokens)
