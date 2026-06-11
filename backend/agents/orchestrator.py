"""
LangGraph StateGraph orchestrator for the Banking CRM Agent.

Graph flow:
  understand_intent → retrieve_customers → [routing] → score_customers
  → filter_top_candidates → [routing] → generate_messages → synthesize_response

Routing rules:
  After retrieve_customers:
    - regenerate_message (has recommended_customers already) → generate_messages
    - no customers / error                                   → synthesize_response
    - default                                               → score_customers

  After filter_top_candidates:
    - explain_customer                                       → synthesize_response
    - no recommended_customers                               → synthesize_response
    - default                                               → generate_messages
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

from backend.agents.state import AgentState
from backend.agents.nodes.query_understanding import understand_intent
from backend.agents.nodes.customer_retrieval import retrieve_customers
from backend.agents.nodes.scoring import score_customers
from backend.agents.nodes.product_recommender import filter_top_candidates
from backend.agents.nodes.message_generator import generate_messages
from backend.agents.nodes.response_synthesizer import synthesize_response

logger = logging.getLogger(__name__)


def _after_retrieve(state: AgentState) -> str:
    """Route after retrieve_customers."""
    intent = state.get("intent", "find_leads")
    error = state.get("error")
    raw = state.get("raw_customers", [])
    recommended = state.get("recommended_customers", [])

    # Greeting — skip everything
    if intent == "greeting":
        return "synthesize_response"

    # Hard stop: nothing to work with
    if error and not raw:
        return "synthesize_response"
    if not raw and not recommended:
        return "synthesize_response"

    # regenerate_message already has recommended_customers set — skip scoring
    if intent == "regenerate_message" and recommended:
        return "generate_messages"

    return "score_customers"


def _after_filter(state: AgentState) -> str:
    """Route after filter_top_candidates."""
    intent = state.get("intent", "find_leads")
    recommended = state.get("recommended_customers", [])

    if not recommended:
        return "synthesize_response"
    if intent in ("explain_customer", "compare_customers", "aggregate_summary"):
        return "synthesize_response"
    return "generate_messages"


def build_graph() -> StateGraph:
    """Construct and compile the LangGraph StateGraph."""
    workflow = StateGraph(AgentState)

    workflow.add_node("understand_intent", understand_intent)
    workflow.add_node("retrieve_customers", retrieve_customers)
    workflow.add_node("score_customers", score_customers)
    workflow.add_node("filter_top_candidates", filter_top_candidates)
    workflow.add_node("generate_messages", generate_messages)
    workflow.add_node("synthesize_response", synthesize_response)

    workflow.set_entry_point("understand_intent")
    workflow.add_edge("understand_intent", "retrieve_customers")

    workflow.add_conditional_edges(
        "retrieve_customers",
        _after_retrieve,
        {
            "score_customers": "score_customers",
            "generate_messages": "generate_messages",
            "synthesize_response": "synthesize_response",
        },
    )
    workflow.add_edge("score_customers", "filter_top_candidates")
    workflow.add_conditional_edges(
        "filter_top_candidates",
        _after_filter,
        {
            "generate_messages": "generate_messages",
            "synthesize_response": "synthesize_response",
        },
    )
    workflow.add_edge("generate_messages", "synthesize_response")
    workflow.add_edge("synthesize_response", END)

    return workflow.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


async def run_agent(query: str, session_id: str = "default") -> Dict[str, Any]:
    """Run agent and return complete result (non-streaming)."""
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

    result = await graph.ainvoke(initial_state)

    return {
        "customers": _serialize_customers(result.get("recommended_customers", [])),
        "messages": result.get("generated_messages", []),
        "reasoning": result.get("reasoning", ""),
        "thinking_steps": result.get("thinking_steps", []),
        "intent": result.get("intent", ""),
        "filters": result.get("filters", {}),
    }


def _serialize_customers(customers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure all customer fields are JSON-serializable."""
    serialized = []
    for c in customers:
        safe = {k: v for k, v in c.items() if k != "transactions"}
        for field in ["conversion_score", "conversion_probability", "monthly_income", "account_balance"]:
            if field in safe and safe[field] is not None:
                safe[field] = round(float(safe[field]), 2)
        serialized.append(safe)
    return serialized
