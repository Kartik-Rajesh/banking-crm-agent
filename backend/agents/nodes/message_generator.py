"""Node 5: Generate personalized WhatsApp messages for top candidates."""

from __future__ import annotations

import logging
from typing import Dict, Any, List

from backend.agents.state import AgentState
from backend.tools.message_tools import generate_whatsapp_messages, validate_message

logger = logging.getLogger(__name__)

DEFAULT_PRODUCT = {
    "name": "Personal Loan - Salaried Standard",
    "interest_rate": "13% - 16%",
    "max_amount": 1000000,
    "usp": "Minimal documentation",
}


def generate_messages(state: AgentState) -> Dict[str, Any]:
    """Generate 3 WhatsApp message variants (formal/casual/urgent) for each recommended customer."""
    recommended = state.get("recommended_customers", [])

    if not recommended:
        return {
            "generated_messages": [],
            "current_step": "generate_messages",
            "thinking_steps": [
                {
                    "type": "thinking",
                    "step": "generate_messages",
                    "message": "No customers to generate messages for.",
                }
            ],
        }

    thinking_step = {
        "type": "thinking",
        "step": "generate_messages",
        "message": (
            f"Crafting personalized WhatsApp messages for {len(recommended)} customer(s) "
            f"— 3 tone variants each (Formal, Casual, Urgent)..."
        ),
        "tool_call": f"generate_whatsapp_messages(customers={len(recommended)}, variants=['formal','casual','urgent'])",
    }

    logger.info("[NODE: message_generator] Calling Groq LLM for %d customers...", len(recommended))

    all_messages: List[Dict[str, Any]] = []

    for customer in recommended:
        product_details = customer.get("product_details") or DEFAULT_PRODUCT

        try:
            variants = generate_whatsapp_messages(customer, product_details)
        except Exception as e:
            logger.error("Message generation failed for %s: %s", customer.get("name"), e)
            first = customer.get("name", "Customer").split()[0]
            variants = [
                {"tone": t, "content": f"Hi {first}, you qualify for a personal loan offer. Reply YES or call [RM_PHONE]"}
                for t in ["formal", "casual", "urgent"]
            ]

        # Log validation results
        for v in variants:
            vr = validate_message(v["content"], customer, product_details)
            if not vr["valid"]:
                logger.warning(
                    "Post-generation validation: %s / %s → %s",
                    customer.get("name"), v["tone"], vr["issues"],
                )
            else:
                logger.debug("Validation OK: %s / %s", customer.get("name"), v["tone"])

        all_messages.append({
            "customer_id": customer["id"],
            "customer_name": customer["name"],
            "product": product_details.get("name", "Personal Loan"),
            "variants": variants,
        })

    thinking_step["message"] += f" — Generated {len(all_messages) * 3} total variants."
    logger.info(
        "[NODE: message_generator] Groq response received: %d messages generated",
        len(all_messages),
    )

    return {
        "generated_messages": all_messages,
        "current_step": "generate_messages",
        "thinking_steps": [thinking_step],
    }
