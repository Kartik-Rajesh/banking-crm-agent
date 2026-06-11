"""
WhatsApp message generation via Groq LLM with compliance validation.

Generates 3 tone variants (formal / casual / urgent) per customer.
Each variant is validated for: customer name, CTA, forbidden terms, length.
Failed messages are regenerated once, then replaced with a safe template.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from backend.llm_factory import get_llm

logger = logging.getLogger(__name__)

# Terms that indicate fabricated banking offers — compliance violation
_FORBIDDEN_TERMS = [
    "waived", "waiver", "rebate", "cashback", "free emi", "guaranteed approval",
    "instant ₹", "0% interest", "emi holiday", "no interest", "interest free",
    "processing fee waived", "salary advance",
]


def _format_amount(amount: float) -> str:
    if amount >= 10_000_000:
        return f"₹{amount / 100_000:.0f} Lakhs"
    if amount >= 100_000:
        return f"₹{amount / 100_000:.1f} Lakhs"
    return f"₹{amount:,.0f}"


def validate_message(msg: str, customer: dict, product: dict) -> dict:
    """Validate a generated WhatsApp message for compliance and quality."""
    issues = []
    first_name = customer.get("name", "Customer").split()[0]

    if first_name.lower() not in msg.lower():
        issues.append("missing_customer_name")

    for term in _FORBIDDEN_TERMS:
        if term.lower() in msg.lower():
            issues.append(f"forbidden_term:{term}")

    if "yes" not in msg.lower() and "call" not in msg.lower():
        issues.append("missing_cta")

    if len(msg) > 500:
        issues.append("too_long")

    return {"message": msg, "valid": len(issues) == 0, "issues": issues}


def _safe_template(customer: dict, product: dict, tone: str) -> str:
    """Compliance-safe fallback template — factual, no invented offers."""
    first_name = customer.get("name", "Customer").split()[0]
    product_name = product.get("name", "Personal Loan")
    rate = product.get("interest_rate", "competitive rates")
    max_amt = _format_amount(product.get("max_amount", 500_000))

    if tone == "formal":
        return (
            f"Dear {first_name}, you have been pre-approved for a {product_name} "
            f"up to {max_amt} at {rate} p.a. "
            f"Reply YES to know more or call your RM."
        )
    if tone == "casual":
        return (
            f"Hi {first_name}! 👋 Great news — you qualify for a {product_name} "
            f"up to {max_amt} at {rate}. "
            f"Reply YES to know more or call your RM 😊"
        )
    return (
        f"Hi {first_name} ⚡ Limited-time offer: {product_name} up to {max_amt} "
        f"at {rate} — act now! "
        f"Reply YES to know more or call your RM 🔥"
    )


def generate_whatsapp_messages(
    customer: Dict[str, Any],
    product: Dict[str, Any],
    llm_available: bool = True,
    enhance_with_llm: bool = True,
) -> List[Dict[str, str]]:
    """
    Generate 3 WhatsApp message variants (formal / casual / urgent) via a single Groq call.
    Falls back to safe templates if the LLM call fails or produces invalid output.
    """
    logger.info("[NODE: message_tools] Calling Groq LLM for customer %s...", customer.get("name", "?"))

    first_name = customer.get("name", "Customer").split()[0]
    occupation = customer.get("occupation", "SALARIED").replace("_", " ").title()
    income = customer.get("monthly_income", 0)
    credit = customer.get("credit_score", 700)
    product_name = product.get("name", "Personal Loan")
    rate = product.get("interest_rate", "13%–16%")
    max_amt = _format_amount(product.get("max_amount", 500_000))
    tenure = product.get("tenure", "")

    # Single LLM call for all 3 tones — 3x fewer API calls vs. per-tone calls
    all_contents = _call_groq_all_tones(
        first_name, occupation, income, credit, product_name, rate, max_amt, tenure, customer, product,
    )

    variants = []
    for tone in ["formal", "casual", "urgent"]:
        content = all_contents.get(tone, "")
        if not content or not validate_message(content, customer, product)["valid"]:
            content = _safe_template(customer, product, tone)
        variants.append({"tone": tone, "content": content})

    logger.info(
        "[NODE: message_tools] Groq response received: %s",
        variants[0]["content"][:100] if variants else "",
    )
    return variants


def _call_groq_all_tones(
    first_name: str,
    occupation: str,
    income: float,
    credit: int,
    product_name: str,
    rate: str,
    max_amt: str,
    tenure: str,
    customer: dict,
    product: dict,
) -> dict:
    """Single Groq call returning all 3 tone variants as a dict."""
    tenure_line = f", repayment tenure {tenure}" if tenure else ""

    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        import json as _json

        system = (
            "You are a banking relationship manager writing WhatsApp messages to customers. "
            "Write naturally as a human banker — never say 'As an AI' or 'I'm an AI'. "
            "Never use placeholder brackets like [NAME] — always use the customer's real name. "
            "Return ONLY a JSON object with keys 'formal', 'casual', 'urgent' — no explanation."
        )

        prompt = (
            f"Write 3 WhatsApp messages from a banking RM to {first_name}.\n"
            f"Customer: {first_name}, {occupation}, monthly income ₹{income:,.0f}, credit score {credit}\n"
            f"Offer: {product_name} up to {max_amt} at {rate} p.a.{tenure_line}\n"
            "\n"
            "STRICT COMPLIANCE RULES:\n"
            f"- ONLY mention these exact product details: {product_name}, {rate} interest rate, up to {max_amt}\n"
            "- Do NOT invent offers, EMI waivers, rebates, cashbacks, or benefits not listed above\n"
            "- Do NOT claim 'instant approval', 'same-day disbursal', or 'guaranteed approval'\n"
            "- Do NOT hallucinate any banking offer — this is a compliance requirement\n"
            "\n"
            "FORMAT RULES for each message:\n"
            f"- Max 3 sentences, use the customer's first name: {first_name}\n"
            f"- End EXACTLY with: 'Reply YES to know more or call your RM'\n"
            "Tones:\n"
            "  formal: professional and respectful, no emojis\n"
            "  casual: warm and friendly with 1-2 emojis\n"
            "  urgent: urgent with a sense of time-sensitivity, 1-2 fire or lightning emojis\n"
            '\nReturn JSON: {"formal": "...", "casual": "...", "urgent": "..."}'
        )

        llm = get_llm(temperature=0.8, max_retries=1)
        response = llm.invoke([SystemMessage(content=system), HumanMessage(content=prompt)])
        raw = response.content.strip()

        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)

        parsed = _json.loads(raw)

        result = {}
        for tone in ("formal", "casual", "urgent"):
            content = parsed.get(tone, "").strip()
            if len(content) > 2 and content[0] == '"' and content[-1] == '"':
                content = content[1:-1].strip()
            content = re.sub(r'\b\d{10,}\b', 'your RM', content)
            content = content.replace('[RM_PHONE]', 'your RM').replace('[RM_CONTACT]', 'your RM')
            if "as an ai" in content.lower() or "i'm an ai" in content.lower():
                content = ""
            result[tone] = content

        return result

    except Exception as e:
        logger.warning("[NODE: message_tools] Groq all-tones call failed: %s", str(e)[:80])
        return {
            "formal": _safe_template(customer, product, "formal"),
            "casual": _safe_template(customer, product, "casual"),
            "urgent": _safe_template(customer, product, "urgent"),
        }
