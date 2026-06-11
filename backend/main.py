"""
Banking CRM Agent — FastAPI application entry point.

Starts the database and registers all routes. Uses Groq as the LLM provider.
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database.seed import init_db
from backend import app_state
from backend.api.chat import router as chat_router
from backend.api.customers import router as customers_router
from backend.api.messages import router as messages_router
from backend.api.settings import router as settings_router

logging.basicConfig(
    stream=sys.stdout,
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Banking CRM Agent...")

    init_db()
    logger.info("Database ready.")

    app_state.llm_provider = settings.llm_provider
    app_state.llm_api_key = settings.groq_api_key
    app_state.llm_model = settings.llm_model

    logger.info("LLM provider: %s / %s", app_state.llm_provider, app_state.llm_model)
    logger.info("Startup complete.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Banking CRM Agent API",
    description="Agentic AI for Personal Loan Conversion — powered by LangGraph + Groq",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(customers_router)
app.include_router(messages_router)
app.include_router(settings_router)


@app.get("/health")
async def health():
    return {"status": "ok", "model": app_state.llm_model, "app": settings.app_name}


@app.get("/api/status")
async def api_status():
    return {
        "status": "ok",
        "llm_available": True,
        "llm_mode": "online",
        "provider": app_state.llm_provider,
        "model": app_state.llm_model,
    }


@app.get("/")
async def root():
    return {
        "message": "Banking CRM Agent API",
        "docs": "/docs",
        "websocket": "ws://localhost:8000/ws/chat",
    }
