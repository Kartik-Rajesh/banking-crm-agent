"""Node 4: Filter top candidates and attach product recommendations."""

from __future__ import annotations

import logging
from typing import Dict, Any

from backend.agents.state import AgentState

logger = logging.getLogger(__name__)

# Minimum score to be considered a viable lead
MIN_VIABLE_SCORE = 40.0


def filter_top_candidates(state: AgentState) -> Dict[str, Any]:
    """Select top N customers by score and attach detailed product recommendations."""
    scored_customers = state.get("scored_customers", [])
    top_n = state.get("top_n", 8)
    intent = state.get("intent", "find_leads")

    thinking_step = {
        "type": "thinking",
        "step": "filter_top_candidates",
        "message": "",
        "tool_call": f"filter_candidates(top_n={top_n}, min_score={MIN_VIABLE_SCORE})",
    }

    if not scored_customers:
        thinking_step["message"] = "No scored customers to filter."
        return {
            "recommended_customers": [],
            "current_step": "filter_top_candidates",
            "thinking_steps": [thinking_step],
        }

    # For deep dive / compare — return all (usually 1 or 2)
    if intent in ("deep_dive", "compare_customers"):
        recommended = scored_customers
        thinking_step["message"] = f"{'Deep-dive' if intent == 'deep_dive' else 'Compare'} mode: returning full analysis for {len(recommended)} customer(s)."
    else:
        # Filter viable + take top N
        viable = [c for c in scored_customers if c.get("conversion_score", 0) >= MIN_VIABLE_SCORE]
        recommended = viable[:top_n]

        if len(recommended) < top_n and len(scored_customers) > len(recommended):
            # Fill with next best even below threshold
            extras = [c for c in scored_customers if c.get("conversion_score", 0) < MIN_VIABLE_SCORE]
            recommended.extend(extras[: top_n - len(recommended)])

        thinking_step["message"] = (
            f"Selected top {len(recommended)} candidates from {len(scored_customers)} scored customers. "
            f"{len(viable)} customers scored above {MIN_VIABLE_SCORE}/100. "
            f"Attaching product recommendations..."
        )

    logger.info(f"Filtered to {len(recommended)} recommended customers")

    return {
        "recommended_customers": recommended,
        "current_step": "filter_top_candidates",
        "thinking_steps": [thinking_step],
    }
