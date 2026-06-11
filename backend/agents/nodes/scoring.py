"""Node 3: Score all retrieved customers using the scoring engine."""

from __future__ import annotations

import logging
from typing import Dict, Any

from backend.agents.state import AgentState
from backend.tools.scoring_tools import score_and_recommend_customers

logger = logging.getLogger(__name__)


def score_customers(state: AgentState) -> Dict[str, Any]:
    """Run the scoring engine on all retrieved customers."""
    raw_customers = state.get("raw_customers", [])
    transactions_by_customer = state.get("transactions_by_customer", {})
    enquiries_by_customer = state.get("enquiries_by_customer", {})

    if not raw_customers:
        return {
            "scored_customers": [],
            "current_step": "score_customers",
            "thinking_steps": [
                {
                    "type": "thinking",
                    "step": "score_customers",
                    "message": "No customers to score.",
                }
            ],
        }

    thinking_step = {
        "type": "thinking",
        "step": "score_customers",
        "message": f"Scoring {len(raw_customers)} customers across 6 weighted factors: income stability, credit score, DTI ratio, account balance, transaction regularity, and loan enquiry recency...",
        "tool_call": f"score_and_recommend_customers(customers={len(raw_customers)}, weights={{income_stability:0.25, credit_score:0.20, dti:0.20, balance:0.15, regularity:0.10, enquiry:0.10}})",
    }

    logger.info(f"Scoring {len(raw_customers)} customers")

    try:
        scored = score_and_recommend_customers(
            customers=raw_customers,
            transactions_by_customer=transactions_by_customer,
            enquiries_by_customer=enquiries_by_customer,
        )

        score_summary = (
            f"Scored {len(scored)} customers. "
            f"Top score: {scored[0]['conversion_score']:.1f}/100 ({scored[0]['name']}). "
            f"Average: {sum(c['conversion_score'] for c in scored) / len(scored):.1f}/100"
        ) if scored else "No customers scored."

        thinking_step["message"] += f" — {score_summary}"

        logger.info(f"Scoring complete. {score_summary}")

        return {
            "scored_customers": scored,
            "current_step": "score_customers",
            "thinking_steps": [thinking_step],
        }

    except Exception as e:
        logger.error(f"Scoring failed: {e}")
        return {
            "scored_customers": raw_customers,  # Return unscored as fallback
            "current_step": "score_customers",
            "thinking_steps": [thinking_step],
            "error": str(e),
        }
