"""
Node 6: Synthesize the final natural language response for the RM.

Primary: Groq LLM for an intelligent executive summary + structured data.
Fallback: rich Python-formatted markdown table if LLM fails.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional

from langchain_core.messages import AIMessage

from backend.agents.state import AgentState
from backend.llm_factory import get_llm

logger = logging.getLogger(__name__)


def synthesize_response(state: AgentState) -> Dict[str, Any]:
    """Build the final RM-facing response."""
    recommended = state.get("recommended_customers", [])
    generated_messages = state.get("generated_messages", [])
    intent = state.get("intent", "find_leads")
    filters = state.get("filters", {})
    rm_query = state.get("rm_query", "")

    thinking_step = {
        "type": "thinking",
        "step": "synthesize_response",
        "message": "Preparing your analysis...",
    }

    logger.info("[NODE: synthesize_response] Calling Groq LLM...")

    response_text = _build_with_llm(recommended, generated_messages, intent, filters, rm_query)

    logger.info("[NODE: synthesize_response] Groq response received: %s", response_text[:100])

    return {
        "reasoning": response_text,
        "current_step": "synthesize_response",
        "thinking_steps": [thinking_step],
        "messages": [AIMessage(content=response_text)],
    }


def _build_with_llm(
    recommended: list,
    generated_messages: list,
    intent: str,
    filters: dict,
    rm_query: str,
) -> str:
    """Use Groq to write the executive summary, then append the structured table."""
    structured = _build_structured(recommended, generated_messages, intent, filters, rm_query)

    # These intents have self-contained templates — no LLM summary needed
    if intent in ("greeting", "compare_customers", "aggregate_summary") or not recommended:
        return structured

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        top = recommended[:3]
        names = ", ".join(c["name"] for c in top)
        scores = ", ".join(f"{c.get('conversion_score', 0):.0f}" for c in top)
        filter_desc = ", ".join(f"{k}={v}" for k, v in filters.items()) or "no filters"
        n = len(recommended)

        system = (
            "You are a senior banking analyst writing executive summaries for relationship managers. "
            "Be specific and data-driven. Never say 'As an AI'. Write as a human analyst."
        )

        prompt = (
            f"Write a 2-sentence executive summary for this CRM analysis.\n"
            f"RM query: '{rm_query}'\n"
            f"Results: {n} candidates found, top 3: {names} (conversion scores: {scores}/100)\n"
            f"Filters applied: {filter_desc}\n"
            f"Be specific about the top candidates and why they stand out. No bullet points. No markdown."
        )

        llm = get_llm(temperature=0.3, max_retries=1)
        response = llm.invoke([
            SystemMessage(content=system),
            HumanMessage(content=prompt),
        ])
        summary = response.content.strip()

        if summary and "as an ai" not in summary.lower():
            return f"> {summary}\n\n---\n\n{structured}"

    except Exception as e:
        logger.warning("[NODE: synthesize_response] LLM summary failed: %s", str(e)[:80])

    return structured


def _build_structured(
    recommended: List[Dict],
    generated_messages: List[Dict],
    intent: str,
    filters: Dict,
    rm_query: str,
) -> str:
    """Build a complete, rich markdown response from pre-computed data."""
    # Greeting
    if intent == "greeting":
        return (
            "## Welcome to Banking CRM Agent\n\n"
            "Hello! I'm your AI-powered CRM assistant. Here's what I can help you with:\n\n"
            "- **Find leads** — *\"Find high-value customers for personal loans\"*\n"
            "- **Filter search** — *\"Show salaried customers in Mumbai with credit score above 720\"*\n"
            "- **Analyse a customer** — *\"Why is Arjun Reddy a good candidate?\"*\n"
            "- **Compare customers** — *\"Compare Arjun Reddy and Tarun Walia\"*\n"
            "- **Generate WhatsApp messages** — *\"Generate urgent messages for top 5 candidates\"*\n"
            "- **Lead summary** — *\"Give me a summary of all leads by priority\"*\n\n"
            "What would you like to do today?"
        )

    # Compare two customers
    if intent == "compare_customers":
        return _build_comparison(recommended)

    # Aggregate summary
    if intent == "aggregate_summary":
        return _build_aggregate(recommended)

    if not recommended:
        return (
            "## No Customers Found\n\n"
            "No customers matched your criteria. "
            "Try broadening the filters — lower the minimum credit score "
            "or expand to other cities."
        )

    n = len(recommended)
    lines = [f"## {n} High-Potential Lead{'s' if n != 1 else ''} Found\n"]

    if filters:
        parts = []
        for k, v in filters.items():
            if k == "min_income":
                parts.append(f"Income ≥ ₹{float(v):,.0f}")
            elif k == "min_credit_score":
                parts.append(f"Credit ≥ {v}")
            elif k == "occupation":
                parts.append(str(v).replace("_", " ").title())
            else:
                parts.append(f"{k.replace('_', ' ').title()}: {v}")
        lines.append(f"*Filters: {', '.join(parts)}*\n")

    lines.append("| # | Name | Score | Conv. Prob | Product | City |")
    lines.append("|---|------|-------|------------|---------|------|")
    for i, c in enumerate(recommended[:10], 1):
        score = c.get("conversion_score", 0)
        prob = c.get("conversion_probability", 0)
        product = c.get("recommended_product", "Personal Loan")
        city = c.get("city", "N/A")
        indicator = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
        lines.append(
            f"| {i} | **{c['name']}** | {indicator} {score:.1f} | {prob:.1f}% | {product} | {city} |"
        )

    lines.append("")

    msg_lookup = {e["customer_name"]: e.get("variants", []) for e in generated_messages}

    lines.append("### Candidate Details\n")
    for i, c in enumerate(recommended[:5], 1):
        total_emi = sum(loan.get("emi", 0) for loan in (c.get("existing_loans") or []))
        dti = round((total_emi / c["monthly_income"] * 100) if c["monthly_income"] > 0 else 0, 1)
        score = c.get("conversion_score", 0)
        prob = c.get("conversion_probability", 0)
        occupation = c.get("occupation", "").replace("_", " ").title()

        lines.append(f"**{i}. {c['name']}** — {score:.1f}/100 ({prob:.1f}% conv. probability)")
        lines.append(
            f"₹{c['monthly_income']:,.0f}/mo | Credit {c['credit_score']} | "
            f"DTI {dti}% | {occupation} | {c.get('city', 'N/A')}"
        )
        lines.append(f"Product: **{c.get('recommended_product', 'Personal Loan')}**")
        if c.get("score_reasoning"):
            lines.append(f"*{c['score_reasoning']}*")

        variants = msg_lookup.get(c["name"], [])
        if variants:
            lines.append("\nWhatsApp Messages:")
            for v in variants:
                lines.append(f"- **{v['tone'].title()}:** {v['content']}")

        lines.append("")

    if generated_messages:
        total = sum(len(e.get("variants", [])) for e in generated_messages)
        lines.append(
            f"✅ {total} WhatsApp variants generated for "
            f"{len(generated_messages)} customer{'s' if len(generated_messages) != 1 else ''} "
            f"(formal · casual · urgent)."
        )

    lines.append("\n### Next Steps")
    lines.append("1. **Prioritize** 🟢 candidates (score > 70) — highest conversion probability.")
    lines.append("2. **Send WhatsApp** — 3 tone variants ready per customer, choose what fits.")
    lines.append("3. **Follow up same day** for customers with recent loan enquiries.")

    return "\n".join(lines)


def _build_comparison(recommended: List[Dict]) -> str:
    """Side-by-side comparison of two customers."""
    if len(recommended) < 2:
        if len(recommended) == 1:
            return (
                f"## Comparison\n\nOnly found one customer: **{recommended[0]['name']}**. "
                "Could not find the second customer for comparison."
            )
        return "## Comparison\n\nCould not find either customer. Please check the names and try again."

    c1, c2 = recommended[0], recommended[1]
    s1 = c1.get("conversion_score", 0)
    s2 = c2.get("conversion_score", 0)
    winner = c1 if s1 >= s2 else c2
    margin = abs(s1 - s2)

    def dti(c: Dict) -> float:
        loans = c.get("existing_loans") or []
        total_emi = sum(loan.get("emi", 0) for loan in loans)
        inc = c.get("monthly_income", 1) or 1
        return round(total_emi / inc * 100, 1)

    ind1 = "🟢" if s1 >= 70 else "🟡" if s1 >= 50 else "🔴"
    ind2 = "🟢" if s2 >= 70 else "🟡" if s2 >= 50 else "🔴"

    lines = [f"## Customer Comparison: {c1['name']} vs {c2['name']}\n"]
    lines.append(f"| Metric | {c1['name']} | {c2['name']} |")
    lines.append(f"|--------|{'—'*len(c1['name'])}|{'—'*len(c2['name'])}|")
    lines.append(f"| **Conversion Score** | {ind1} **{s1:.1f}/100** | {ind2} **{s2:.1f}/100** |")
    lines.append(f"| Conv. Probability | {c1.get('conversion_probability', 0):.1f}% | {c2.get('conversion_probability', 0):.1f}% |")
    lines.append(f"| Monthly Income | ₹{c1.get('monthly_income', 0):,.0f} | ₹{c2.get('monthly_income', 0):,.0f} |")
    lines.append(f"| Credit Score | {c1.get('credit_score', 0)} | {c2.get('credit_score', 0)} |")
    lines.append(f"| DTI Ratio | {dti(c1)}% | {dti(c2)}% |")
    lines.append(f"| Occupation | {c1.get('occupation','').replace('_',' ').title()} | {c2.get('occupation','').replace('_',' ').title()} |")
    lines.append(f"| City | {c1.get('city','N/A')} | {c2.get('city','N/A')} |")
    lines.append(f"| Product | {c1.get('recommended_product','Personal Loan')} | {c2.get('recommended_product','Personal Loan')} |")
    lines.append("")

    gap_desc = f"by {margin:.1f} points" if margin >= 1 else "by a very thin margin"
    lines.append(f"### Recommendation\n")
    lines.append(f"**Approach {winner['name']} first** — leads {gap_desc} with a conversion score of {max(s1, s2):.1f}/100.")

    if c1.get("score_reasoning"):
        lines.append(f"\n*{c1['name']}: {c1['score_reasoning']}*")
    if c2.get("score_reasoning"):
        lines.append(f"*{c2['name']}: {c2['score_reasoning']}*")

    return "\n".join(lines)


def _build_aggregate(recommended: List[Dict]) -> str:
    """Overall pipeline summary — lead counts by priority tier."""
    if not recommended:
        return (
            "## Lead Summary\n\n"
            "No customers found in the database. Please check the data source."
        )

    high = [c for c in recommended if c.get("conversion_score", 0) >= 70]
    med  = [c for c in recommended if 50 <= c.get("conversion_score", 0) < 70]
    low  = [c for c in recommended if c.get("conversion_score", 0) < 50]

    avg_score = sum(c.get("conversion_score", 0) for c in recommended) / len(recommended)
    top = recommended[0]

    lines = [f"## Lead Pipeline Summary — {len(recommended)} Customers Analyzed\n"]
    lines.append(f"| Priority | Count | Avg Score | Action |")
    lines.append(f"|----------|-------|-----------|--------|")
    lines.append(f"| 🟢 High (≥70) | **{len(high)}** | {sum(c.get('conversion_score',0) for c in high)/max(len(high),1):.1f} | Immediate outreach |")
    lines.append(f"| 🟡 Medium (50–69) | **{len(med)}** | {sum(c.get('conversion_score',0) for c in med)/max(len(med),1):.1f} | Nurture this week |")
    lines.append(f"| 🔴 Low (<50) | **{len(low)}** | {sum(c.get('conversion_score',0) for c in low)/max(len(low),1):.1f} | Long-term pipeline |")
    lines.append("")
    lines.append(f"**Pipeline average score:** {avg_score:.1f}/100")
    lines.append(f"**Top candidate:** {top['name']} — {top.get('conversion_score',0):.1f}/100 ({top.get('recommended_product','Personal Loan')})\n")

    if high:
        lines.append("### 🟢 High Priority — Approach Immediately")
        for c in high[:5]:
            lines.append(f"- **{c['name']}** — {c.get('conversion_score',0):.1f}/100 | ₹{c.get('monthly_income',0):,.0f}/mo | {c.get('city','N/A')}")
        lines.append("")

    lines.append("### Next Steps")
    lines.append(f"1. Contact the **{len(high)} high-priority** leads today with personalized WhatsApp messages.")
    lines.append(f"2. Schedule follow-ups for the **{len(med)} medium-priority** leads this week.")
    lines.append(f"3. Monitor **{len(low)} low-priority** leads for credit score or income improvements.")

    return "\n".join(lines)
