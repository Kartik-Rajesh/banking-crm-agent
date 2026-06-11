"""Node 2: Retrieve customers from DB based on parsed filters."""

from __future__ import annotations

import logging
from typing import Dict, Any

from backend.agents.state import AgentState
from backend.tools.db_tools import get_customers_by_criteria, get_customer_by_name

logger = logging.getLogger(__name__)

# Intents that operate on a single named customer
_SINGLE_CUSTOMER_INTENTS = ("deep_dive", "explain_customer", "regenerate_message")
# Intents that need no DB retrieval
_NO_RETRIEVAL_INTENTS = ("greeting",)


def retrieve_customers(state: AgentState) -> Dict[str, Any]:
    """Fetch customers from the database matching the RM's criteria."""
    filters = state.get("filters", {})
    intent = state.get("intent", "find_leads")
    target_name = state.get("target_customer_name")

    thinking_step = {
        "type": "thinking",
        "step": "retrieve_customers",
        "message": _build_thinking_message(intent, filters, target_name),
        "tool_call": _build_tool_call_description(intent, filters, target_name),
    }

    logger.info("Retrieving customers. Intent=%s, Filters=%s", intent, filters)

    try:
        # Greeting — no DB needed
        if intent in _NO_RETRIEVAL_INTENTS:
            return {
                "raw_customers": [],
                "recommended_customers": [],
                "transactions_by_customer": {},
                "enquiries_by_customer": {},
                "current_step": "retrieve_customers",
                "thinking_steps": [thinking_step],
            }

        if intent in _SINGLE_CUSTOMER_INTENTS and target_name:
            return _retrieve_single(target_name, intent, thinking_step)

        # Compare two named customers
        if intent == "compare_customers" and target_name:
            target_2 = state.get("target_customer_name_2")
            return _retrieve_compare(target_name, target_2, thinking_step)

        # Multi-customer retrieval with filters
        result = get_customers_by_criteria(
            city=filters.get("city"),
            min_income=filters.get("min_income"),
            max_income=filters.get("max_income"),
            min_credit_score=filters.get("min_credit_score"),
            max_credit_score=filters.get("max_credit_score"),
            occupation=filters.get("occupation"),
            days_since_enquiry=filters.get("days_since_enquiry"),
            limit=50,
        )

        logger.info("Retrieved %d customers from database", result["total"])
        if result["total"] == 0:
            thinking_step["message"] += " — No customers found. Suggest broadening filters."

        return {
            "raw_customers": result["customers"],
            "recommended_customers": [],
            "transactions_by_customer": {int(k): v for k, v in result["transactions_by_customer"].items()},
            "enquiries_by_customer": {int(k): v for k, v in result["enquiries_by_customer"].items()},
            "current_step": "retrieve_customers",
            "thinking_steps": [thinking_step],
        }

    except Exception as e:
        logger.error("Customer retrieval failed: %s", e)
        return {
            "raw_customers": [],
            "recommended_customers": [],
            "transactions_by_customer": {},
            "enquiries_by_customer": {},
            "current_step": "retrieve_customers",
            "thinking_steps": [thinking_step],
            "error": str(e),
        }


def _retrieve_single(target_name: str, intent: str, thinking_step: dict) -> Dict[str, Any]:
    """Fetch one customer by name. For regenerate_message, also scores them immediately."""
    customer_data = get_customer_by_name(target_name)
    if not customer_data:
        return {
            "raw_customers": [],
            "recommended_customers": [],
            "transactions_by_customer": {},
            "enquiries_by_customer": {},
            "current_step": "retrieve_customers",
            "thinking_steps": [thinking_step],
            "error": f"Customer '{target_name}' not found in database.",
        }

    transactions = customer_data.pop("transactions", [])
    enquiries = customer_data.pop("loan_enquiries", [])

    base = {
        "raw_customers": [customer_data],
        "transactions_by_customer": {customer_data["id"]: transactions},
        "enquiries_by_customer": {customer_data["id"]: enquiries},
        "current_step": "retrieve_customers",
        "thinking_steps": [thinking_step],
    }

    if intent == "regenerate_message":
        # Score immediately so we can skip the score/filter nodes
        from backend.tools.scoring_tools import score_customer, recommend_product
        scored = score_customer(customer_data, transactions, enquiries)
        product = recommend_product(scored)
        scored["recommended_product"] = product["name"] if product else "Personal Loan"
        scored["product_details"] = product
        base["recommended_customers"] = [scored]
    else:
        base["recommended_customers"] = []

    return base


def _build_thinking_message(intent: str, filters: Dict, target_name: str | None) -> str:
    if intent in _SINGLE_CUSTOMER_INTENTS and target_name:
        action = {
            "deep_dive": "deep dive on",
            "explain_customer": "profile analysis for",
            "regenerate_message": "fetching profile for",
        }.get(intent, "fetching")
        return f"Fetching {action} customer '{target_name}' including transaction history..."

    filter_parts = []
    if filters.get("city"):
        filter_parts.append(f"city={filters['city']}")
    if filters.get("min_income"):
        filter_parts.append(f"income≥₹{filters['min_income']:,.0f}")
    if filters.get("min_credit_score"):
        filter_parts.append(f"credit≥{filters['min_credit_score']}")
    if filters.get("occupation"):
        filter_parts.append(f"occupation={filters['occupation']}")
    if filter_parts:
        return f"Querying database with filters: {', '.join(filter_parts)}..."
    return "Querying database for all eligible customers..."


def _build_tool_call_description(intent: str, filters: Dict, target_name: str | None) -> str:
    if intent in _SINGLE_CUSTOMER_INTENTS and target_name:
        return f"get_customer_by_name(name='{target_name}')"
    parts = [f"{k}={repr(v)}" for k, v in filters.items() if v is not None]
    return f"get_customers_by_criteria({', '.join(parts)})"


def _retrieve_compare(name1: str, name2: str | None, thinking_step: dict) -> Dict[str, Any]:
    """Fetch two named customers for side-by-side comparison."""
    customers = []
    transactions_map: Dict[int, list] = {}
    enquiries_map: Dict[int, list] = {}

    for name in filter(None, [name1, name2]):
        data = get_customer_by_name(name)
        if data:
            txns = data.pop("transactions", [])
            enqs = data.pop("loan_enquiries", [])
            customers.append(data)
            transactions_map[data["id"]] = txns
            enquiries_map[data["id"]] = enqs

    if not customers:
        return {
            "raw_customers": [],
            "recommended_customers": [],
            "transactions_by_customer": {},
            "enquiries_by_customer": {},
            "current_step": "retrieve_customers",
            "thinking_steps": [thinking_step],
            "error": f"Could not find customers '{name1}' and '{name2}'.",
        }

    thinking_step["message"] = f"Fetching profiles for {', '.join(c['name'] for c in customers)}..."
    return {
        "raw_customers": customers,
        "recommended_customers": [],
        "transactions_by_customer": transactions_map,
        "enquiries_by_customer": enquiries_map,
        "current_step": "retrieve_customers",
        "thinking_steps": [thinking_step],
    }
