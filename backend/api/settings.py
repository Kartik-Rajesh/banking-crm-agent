"""
Runtime LLM configuration endpoint.

POST /api/settings/llm-mode  — switch provider / API key / model without restarting.
GET  /api/settings/providers  — list supported providers and their models.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend import app_state
from backend.llm_factory import invalidate, get_llm, PROVIDER_MODELS, DEFAULT_MODEL

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/settings", tags=["settings"])


class LLMModeRequest(BaseModel):
    mode: str                      # "online" | "offline"
    provider: Optional[str] = None # "gemini" | "groq" | "anthropic"
    api_key: Optional[str] = None
    model: Optional[str] = None


@router.get("/providers")
async def list_providers():
    """Return supported providers and their available models."""
    return {
        "providers": [
            {
                "id": pid,
                "label": {"gemini": "Gemini", "groq": "Groq", "anthropic": "Anthropic"}[pid],
                "subtitle": {"gemini": "Google AI", "groq": "Groq Cloud", "anthropic": "Claude"}[pid],
                "models": models,
                "default_model": DEFAULT_MODEL[pid],
                "key_placeholder": {
                    "gemini": "AIzaSy...",
                    "groq": "gsk_...",
                    "anthropic": "sk-ant-...",
                }[pid],
            }
            for pid, models in PROVIDER_MODELS.items()
        ]
    }


@router.post("/llm-mode")
async def set_llm_mode(req: LLMModeRequest):
    """Switch LLM provider / API key / model at runtime. Runs a test call and reports result."""
    if req.provider and req.provider in PROVIDER_MODELS:
        app_state.llm_provider = req.provider
        if not req.model:
            app_state.llm_model = DEFAULT_MODEL[req.provider]

    if req.api_key and req.api_key.strip():
        app_state.llm_api_key = req.api_key.strip()

    if req.model and req.model.strip():
        app_state.llm_model = req.model.strip()

    invalidate()

    result = await asyncio.to_thread(_test_connection)

    logger.info(
        "LLM settings updated: %s — provider=%s model=%s",
        "OK" if result["success"] else "FAIL",
        app_state.llm_provider,
        app_state.llm_model,
    )

    return {
        "success": result["success"],
        "llm_available": result["success"],
        "llm_mode": "online",
        "provider": app_state.llm_provider,
        "model": app_state.llm_model,
        "message": result.get("message", ""),
        "error": result.get("error", ""),
    }


def _test_connection() -> dict:
    """Synchronous LLM probe — run inside a thread."""
    try:
        from langchain_core.messages import HumanMessage

        llm = get_llm(temperature=0, max_retries=0)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(llm.invoke, [HumanMessage(content="Reply with just: OK")])
            future.result(timeout=8)

        return {
            "success": True,
            "message": f"Connected to {app_state.llm_provider} ({app_state.llm_model})",
        }
    except Exception as exc:
        err = str(exc)
        if "quota" in err.lower() or "429" in err:
            clean = "API quota exceeded. Try a paid-tier key or a different model."
        elif "api key" in err.lower() or "api_key" in err.lower() or "401" in err or "403" in err:
            clean = "Invalid API key. Check the key and try again."
        elif "not found" in err.lower() or "404" in err:
            clean = f"Model '{app_state.llm_model}' not found for this API key. Try a different model."
        elif "not installed" in err.lower():
            clean = err
        else:
            clean = err[:180]
        return {"success": False, "error": clean}
