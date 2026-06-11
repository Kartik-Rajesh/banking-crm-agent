"""LangGraph agent state definition."""

from __future__ import annotations

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    """State shared across all LangGraph nodes."""

    messages: Annotated[List[BaseMessage], operator.add]
    rm_query: str
    intent: str           # find_leads | filtered_search | deep_dive | regenerate_message | explain_customer
    filters: Dict[str, Any]
    raw_customers: List[Dict[str, Any]]
    transactions_by_customer: Dict[int, List[Dict[str, Any]]]
    enquiries_by_customer: Dict[int, List[Dict[str, Any]]]
    scored_customers: List[Dict[str, Any]]
    recommended_customers: List[Dict[str, Any]]
    generated_messages: List[Dict[str, Any]]
    target_customer_name: Optional[str]
    target_customer_name_2: Optional[str]  # second customer for compare_customers
    requested_tone: Optional[str]     # "formal" | "casual" | "urgent" | None
    reasoning: str
    current_step: str
    thinking_steps: List[Dict[str, str]]
    error: Optional[str]
    top_n: int
