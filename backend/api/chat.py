"""
WebSocket endpoint for streaming agent interactions.

Uses a single graph.astream() pass — emits customers and messages progressively
as each node completes, so the right panel updates without waiting for the full run.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator, Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from pydantic import BaseModel

from backend.agents.orchestrator import run_agent, _serialize_customers

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory session state: session_id → {"customers": [...], "messages": [...]}
_session_cache: dict = {}

_FOLLOWUP_PHRASES = [
    "all of them", "for them", "for all", "same customers", "those customers",
    "generate for all", "messages for all", "make it urgent", "make them urgent",
    "now send", "send all", "generate messages now",
]


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent streaming.

    Client sends: {"message": "...", "session_id": "..."}
    Server streams: thinking steps, customers_ready, partial_result (messages), text, done.
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
                query = data.get("message", "").strip()
                session_id = data.get("session_id", "default")
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON payload"})
                continue

            if not query:
                await websocket.send_json({"type": "error", "message": "Empty message"})
                continue

            logger.info("Processing query: %s (session=%s)", query[:100], session_id)

            await websocket.send_json({
                "type": "thinking",
                "step": "start",
                "message": "Agent is analyzing your request...",
            })

            async for chunk in _stream_agent(query, session_id):
                try:
                    await websocket.send_json(chunk)
                except Exception as send_err:
                    logger.error("Failed to send chunk: %s", send_err)
                    break

            await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error("WebSocket error: %s", e, exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": f"Server error: {str(e)}"})
        except Exception:
            pass


async def _stream_agent(query: str, session_id: str) -> AsyncIterator[Dict[str, Any]]:
    """
    Single-pass agent stream.

    Emits customers_ready immediately after filter_top_candidates completes,
    then messages via partial_result after generate_messages completes.
    Handles follow-up queries by re-using prior session customers.
    """
    from backend.agents.orchestrator import get_graph
    from langchain_core.messages import HumanMessage
    from backend.agents.state import AgentState

    # ── Follow-up shortcut ──────────────────────────────────────────────────
    q_lower = query.lower()
    prior = _session_cache.get(session_id, {})
    is_followup = bool(prior.get("customers")) and any(p in q_lower for p in _FOLLOWUP_PHRASES)

    if is_followup:
        prior_customers = prior["customers"]
        tone = next((t for t in ["urgent", "casual", "formal"] if t in q_lower), None)
        logger.info(
            "Follow-up query detected (session=%s): re-generating messages for %d customers, tone=%s",
            session_id, len(prior_customers), tone,
        )

        yield {"type": "thinking", "step": "start", "message": "Agent is analyzing your request..."}
        yield {"type": "thinking", "step": "understand_intent", "message": "Detected follow-up — re-using prior customers"}
        yield {"type": "customers_ready", "customers": prior_customers}
        await asyncio.sleep(0.1)
        yield {"type": "thinking", "step": "generate_messages",
               "message": f"Crafting messages for {len(prior_customers)} customer(s) — tone: {tone or 'all'}"}

        from backend.tools.message_tools import generate_whatsapp_messages
        msgs = []
        for cust in prior_customers:
            product = cust.get("product_details") or {}
            generated = generate_whatsapp_messages(
                customer=cust,
                product=product,
            )
            msgs.append({
                "customer_id":   cust.get("id"),
                "customer_name": cust.get("name"),
                "product":       product.get("name") or cust.get("recommended_product"),
                "variants":      generated,
            })

        yield {"type": "partial_result", "messages": msgs}
        await asyncio.sleep(0)
        yield {"type": "thinking", "step": "synthesize_response", "message": "Preparing your analysis..."}

        names = ", ".join(c.get("name","") for c in prior_customers[:3])
        extra = f" and {len(prior_customers)-3} more" if len(prior_customers) > 3 else ""
        yield {"type": "text", "content": f"Generated {'urgent ' if tone=='urgent' else ''}WhatsApp messages for {names}{extra}."}
        yield {"type": "result", "customers": prior_customers, "messages": msgs, "intent": "regenerate_message", "filters": {}}
        _session_cache[session_id] = {"customers": prior_customers, "messages": msgs}
        return
    # ────────────────────────────────────────────────────────────────────────

    graph = get_graph()

    initial_state: AgentState = {
        "messages": [HumanMessage(content=query)],
        "rm_query": query,
        "intent": "",
        "filters": {},
        "raw_customers": [],
        "transactions_by_customer": {},
        "enquiries_by_customer": {},
        "scored_customers": [],
        "recommended_customers": [],
        "generated_messages": [],
        "target_customer_name": None,
        "target_customer_name_2": None,
        "requested_tone": None,
        "reasoning": "",
        "current_step": "start",
        "thinking_steps": [],
        "error": None,
        "top_n": 8,
    }

    acc: Dict[str, Any] = {
        "recommended_customers": [],
        "generated_messages": [],
        "reasoning": "",
        "filters": {},
        "intent": "",
    }

    try:
        async for chunk in graph.astream(initial_state, stream_mode="updates"):
            for node_name, node_output in chunk.items():
                # Emit thinking steps from this node
                for step in node_output.get("thinking_steps", []):
                    yield step
                    await asyncio.sleep(0)

                # customers_ready — emit immediately after filter_top_candidates or retrieve (for regen)
                if node_output.get("recommended_customers"):
                    acc["recommended_customers"] = node_output["recommended_customers"]
                    # Eagerly populate session cache so follow-up queries work even if
                    # the client disconnects before generate_messages completes
                    _session_cache[session_id] = {
                        "customers": _serialize_customers(acc["recommended_customers"]),
                        "messages":  [],
                    }
                    yield {
                        "type": "customers_ready",
                        "customers": _serialize_customers(acc["recommended_customers"]),
                    }
                    # Explicit sleep to let the event loop flush this to the client
                    # before the (potentially slow) generate_messages node starts
                    await asyncio.sleep(0.15)

                # messages partial_result — after generate_messages
                if node_output.get("generated_messages"):
                    acc["generated_messages"] = node_output["generated_messages"]
                    # Update session cache with generated messages
                    if session_id in _session_cache:
                        _session_cache[session_id]["messages"] = acc["generated_messages"]
                    yield {
                        "type": "partial_result",
                        "messages": acc["generated_messages"],
                    }
                    await asyncio.sleep(0)

                # Accumulate scalars
                if node_output.get("filters") is not None:
                    acc["filters"] = node_output["filters"]
                if node_output.get("intent"):
                    acc["intent"] = node_output["intent"]
                if node_output.get("reasoning"):
                    acc["reasoning"] = node_output["reasoning"]

    except Exception as e:
        logger.error("Graph execution error: %s", e, exc_info=True)
        yield {"type": "error", "message": str(e)}
        return

    # Persist session state for follow-up queries
    if acc["recommended_customers"]:
        _session_cache[session_id] = {
            "customers": _serialize_customers(acc["recommended_customers"]),
            "messages":  acc["generated_messages"],
        }

    # Final consolidated result
    yield {
        "type": "result",
        "customers": _serialize_customers(acc["recommended_customers"]),
        "messages": acc["generated_messages"],
        "filters": acc["filters"],
        "intent": acc["intent"],
    }

    if acc["reasoning"]:
        yield {"type": "text", "content": acc["reasoning"]}


@router.post("/api/chat")
async def chat_rest(request: ChatRequest):
    """REST fallback for chat — returns complete response without streaming."""
    try:
        result = await run_agent(request.message, request.session_id)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error("REST chat failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
