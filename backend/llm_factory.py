"""
Provider-agnostic LLM factory with settings-aware caching.

Supports Gemini, Groq, and Anthropic. The cache is keyed on a version counter
that increments whenever settings change, so nodes always get an up-to-date instance.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_cache: dict = {}
_version: int = 0

PROVIDER_MODELS: dict[str, list[str]] = {
    "gemini": [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-2.5-flash",
    ],
    "groq": [
        "llama-3.1-8b-instant",
        "llama-3.1-70b-versatile",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
    ],
    "anthropic": [
        "claude-haiku-4-5-20251001",
        "claude-3-5-haiku-20241022",
        "claude-3-5-sonnet-20241022",
    ],
}

DEFAULT_MODEL: dict[str, str] = {
    "gemini": "gemini-2.0-flash",
    "groq": "llama-3.1-8b-instant",
    "anthropic": "claude-haiku-4-5-20251001",
}


def invalidate() -> None:
    """Call whenever provider / api_key / model changes at runtime."""
    global _version
    _version += 1
    _cache.clear()
    logger.info("LLM cache invalidated (v%d)", _version)


def get_llm(temperature: float = 0, max_retries: int = 0) -> Any:
    """Return a cached LLM instance matching the current app_state settings."""
    from backend import app_state

    key = (_version, app_state.llm_provider, app_state.llm_api_key,
           app_state.llm_model, temperature, max_retries)

    if key not in _cache:
        _cache[key] = _build(
            provider=app_state.llm_provider,
            api_key=app_state.llm_api_key,
            model=app_state.llm_model,
            temperature=temperature,
            max_retries=max_retries,
        )
        logger.debug("Built LLM: %s / %s (temp=%.1f)", app_state.llm_provider, app_state.llm_model, temperature)

    return _cache[key]


def _build(provider: str, api_key: str, model: str, temperature: float, max_retries: int) -> Any:
    if provider == "gemini":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise RuntimeError("Package not installed. Run: pip install langchain-google-genai")
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
            max_retries=max_retries,
        )

    if provider == "groq":
        try:
            from langchain_groq import ChatGroq
        except ImportError:
            raise RuntimeError("Package not installed. Run: pip install langchain-groq")
        return ChatGroq(
            model=model,
            groq_api_key=api_key,
            temperature=temperature,
            max_retries=max_retries,
        )

    if provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise RuntimeError("Package not installed. Run: pip install langchain-anthropic")
        return ChatAnthropic(
            model=model,
            anthropic_api_key=api_key,
            temperature=temperature,
            max_retries=max_retries,
        )

    raise ValueError(f"Unknown provider '{provider}'. Choose: gemini, groq, anthropic")
