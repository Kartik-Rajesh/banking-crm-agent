"""
Node 1: Parse the RM's natural language query into structured intent + filters.

Uses Groq LLM for intelligent intent parsing. Falls back to regex on failure.
Supported intents:
  find_leads         — general high-value lead search
  filtered_search    — leads with specific filters (city / income / credit / occupation)
  deep_dive          — detailed analysis of a specific named customer
  regenerate_message — generate/regenerate WhatsApp messages for a specific customer
  explain_customer   — explain why a specific customer is (or isn't) a good candidate
  compare_customers  — side-by-side comparison of two named customers
  aggregate_summary  — statistics/breakdown of all leads by priority tier
  greeting           — casual greeting with no business intent
"""

from __future__ import annotations

import json
import logging
import re
from typing import Dict, Any

from backend.agents.state import AgentState

logger = logging.getLogger(__name__)


def understand_intent(state: AgentState) -> Dict[str, Any]:
    """Parse RM query into structured intent and filters using Groq LLM."""
    query = state["rm_query"]
    logger.info("[NODE: understand_intent] Calling Groq LLM...")

    thinking_step = {
        "type": "thinking",
        "step": "understand_intent",
        "message": "Analyzing your query...",
    }

    # High-confidence regex pre-check: intercept patterns LLM often misclassifies
    parsed = _pre_check_patterns(query) or _parse_with_llm(query)

    top_n = int(parsed.get("top_n") or 8)
    top_n = max(1, min(top_n, 20))

    filters = {
        k: parsed[k]
        for k in ["city", "min_income", "max_income", "min_credit_score", "max_credit_score", "occupation"]
        if parsed.get(k) is not None
    }
    if parsed.get("days_since_enquiry") is not None:
        filters["days_since_enquiry"] = int(parsed["days_since_enquiry"])

    intent = parsed["intent"]
    target = parsed.get("target_customer_name")
    target_2 = parsed.get("target_customer_name_2")
    tone = parsed.get("requested_tone")

    # Aggregate summary scans all customers
    if intent == "aggregate_summary":
        top_n = 50

    logger.info(
        "[NODE: understand_intent] Groq response received: intent=%s target=%s target2=%s tone=%s filters=%s top_n=%d",
        intent, target, target_2, tone, filters, top_n,
    )

    return {
        "intent": intent,
        "filters": filters,
        "top_n": top_n,
        "target_customer_name": target,
        "target_customer_name_2": target_2,
        "requested_tone": tone,
        "current_step": "understand_intent",
        "thinking_steps": [thinking_step],
    }


def _pre_check_patterns(query: str) -> Dict[str, Any] | None:
    """
    Fast, deterministic pre-check for high-confidence patterns.
    Returns a parsed dict if matched, None to fall through to LLM.
    """
    q = query.lower().strip()

    # Greeting
    if re.match(r'^(hi|hello|hey|howdy|greetings?|good\s+(?:morning|afternoon|evening|day))[\s!\.,]*$', q):
        return _empty_parsed("greeting")

    # Compare two named customers — deterministic with names
    m = re.search(
        r'\bcompare\s+([A-Za-z]+ [A-Za-z]+)\s+(?:and|vs\.?|versus|with)\s+([A-Za-z]+ [A-Za-z]+)',
        query, re.IGNORECASE,
    )
    if not m:
        m = re.search(
            r'([A-Za-z]+ [A-Za-z]+)\s+(?:vs\.?|versus)\s+([A-Za-z]+ [A-Za-z]+)',
            query, re.IGNORECASE,
        )
    if m:
        p = _empty_parsed("compare_customers")
        p["target_customer_name"] = m.group(1).strip().title()
        p["target_customer_name_2"] = m.group(2).strip().title()
        return p

    # Aggregate summary — keywords that LLM often misclassifies as find_leads
    if re.search(
        r'\b(how many|give me a (full\s+)?summary|breakdown|pipeline summary|all leads|'
        r'high.*medium.*low|low.*medium.*high|priority leads|lead tiers?|lead stats)\b',
        q,
    ):
        p = _empty_parsed("aggregate_summary")
        p["top_n"] = 50
        return p

    # Single-customer message regeneration — deterministic to avoid LLM timeouts
    m = re.search(
        r'\bregenerat(?:e|ing)\b.{0,40}?(?:whatsapp\s+)?messages?\s+for\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        query, re.IGNORECASE,
    )
    if not m:
        m = re.search(
            r'\bregenerat(?:e|ing)\b.{0,40}?for\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            query, re.IGNORECASE,
        )
    if m:
        p = _empty_parsed("regenerate_message")
        p["target_customer_name"] = m.group(1).strip().title()
        for tone in ("urgent", "casual", "formal"):
            if tone in q:
                p["requested_tone"] = tone
                break
        return p

    # Bulk message generation — guard against LLM hallucinating regenerate_message
    # Matches: "generate messages for top N", "find customers ... generate messages", etc.
    is_bulk_customers = bool(re.search(r'\bcustomers?\b', q))
    is_generate_msgs = bool(re.search(r'\b(generate|create|send)\b.*\b(message|whatsapp)\b', q))
    is_top_n_msgs = bool(
        re.search(r'\bgenerate\b.*\bmessages?\b.*\btop\s+\d+\b', q) or
        re.search(r'\btop\s+\d+\b.*\b(generate|send|create)\b.*\bmessages?\b', q)
    )
    if is_top_n_msgs or (is_bulk_customers and is_generate_msgs):
        p = _empty_parsed("find_leads")
        n_m = re.search(r'\btop\s+(\d+)\b', q)
        if n_m:
            p["top_n"] = int(n_m.group(1))
        for tone in ("urgent", "casual", "formal"):
            if tone in q:
                p["requested_tone"] = tone
                break
        return p

    return None


def _empty_parsed(intent: str) -> Dict[str, Any]:
    return {
        "intent": intent,
        "city": None, "min_income": None, "max_income": None,
        "min_credit_score": None, "max_credit_score": None,
        "occupation": None, "days_since_enquiry": None,
        "top_n": 8, "target_customer_name": None,
        "target_customer_name_2": None, "requested_tone": None,
    }


def _parse_with_llm(query: str) -> Dict[str, Any]:
    """Use Groq to parse the query. Falls back to regex on any failure."""
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from backend.llm_factory import get_llm

        system = (
            "You are a query parser for a banking CRM. Extract intent and filters from the RM's query.\n"
            "Return ONLY valid JSON with these fields (use null for missing values):\n"
            "{\n"
            '  "intent": "find_leads" | "filtered_search" | "deep_dive" | "regenerate_message" | "explain_customer" | "compare_customers" | "aggregate_summary" | "greeting",\n'
            '  "city": string | null,\n'
            '  "min_income": number | null,\n'
            '  "max_income": number | null,\n'
            '  "min_credit_score": number | null,\n'
            '  "max_credit_score": number | null,\n'
            '  "occupation": "SALARIED" | "SELF_EMPLOYED" | null,\n'
            '  "days_since_enquiry": number | null,\n'
            '  "top_n": number | null,\n'
            '  "target_customer_name": string | null,\n'
            '  "target_customer_name_2": string | null,\n'
            '  "requested_tone": "formal" | "casual" | "urgent" | null\n'
            "}\n"
            "Intent rules:\n"
            "- 'filtered_search' if any filter (city/income/credit/occupation/days_since_enquiry) is present\n"
            "- 'deep_dive' ONLY if asking about a named customer's profile/analysis without message request\n"
            "- 'regenerate_message' if user wants to generate/regenerate WhatsApp messages for a specific named customer\n"
            "- 'explain_customer' if asking WHY a named customer is a good/bad candidate, or 'tell me about [Name]'\n"
            "- 'compare_customers' if comparing/contrasting TWO named customers (e.g. 'compare X and Y', 'X vs Y', 'who should I approach first'). Set target_customer_name=first person, target_customer_name_2=second person.\n"
            "- 'aggregate_summary' if asking for overall statistics/breakdown of all leads (e.g. 'how many leads', 'give me a summary', 'high medium low priority', 'breakdown', 'how many customers').\n"
            "- 'greeting' if the query is a casual greeting with no business intent (e.g. 'hello', 'hi', 'hey', 'good morning').\n"
            "- 'find_leads' as the default for general searches\n"
            "- Income values in full rupees (1 lakh = 100000)\n"
            "- Income direction: 'above X', 'over X', 'more than X', 'at least X', '>X', 'exceeding X' → min_income=X; "
            "'below X', 'under X', 'less than X', '<X' → max_income=X\n"
            "- Credit score direction: 'above X', 'over X', 'more than X', 'at least X', '>X' → min_credit_score=X; "
            "'below X', 'under X', 'less than X' → max_credit_score=X\n"
            "- Days since enquiry: 'last X days', 'past X days', 'within X days', 'in the last X days' → days_since_enquiry=X\n"
            "- City aliases: 'New Delhi' → 'Delhi', 'Bombay' → 'Mumbai', 'Bengaluru' → 'Bangalore'\n"
            "- Occupation aliases: 'business owners', 'entrepreneurs', 'freelancers', 'self employed' → 'SELF_EMPLOYED'\n"
            "- IMPORTANT: Do NOT set min_income or max_income from vague qualitative terms like "
            "'high-value', 'premium', 'top-tier', 'high-net-worth', 'quality', 'good candidates'. "
            "Only set income filters when the user gives an EXPLICIT number (e.g. 'above 1.5 lakh', '> 2,00,000').\n"
            "- IMPORTANT: For find_leads, filtered_search, aggregate_summary — do NOT set target_customer_name.\n"
            "- Extract customer name ONLY for regenerate_message, explain_customer, deep_dive, compare_customers.\n"
            "Return ONLY the JSON object, no explanation"
        )

        llm = get_llm(temperature=0, max_retries=1)
        response = llm.invoke([
            SystemMessage(content=system),
            HumanMessage(content=query),
        ])
        content = response.content.strip()

        if content.startswith("```"):
            content = re.sub(r"^```[a-z]*\n?", "", content)
            content = re.sub(r"\n?```$", "", content)

        parsed = json.loads(content)
        parsed.setdefault("intent", "find_leads")
        parsed.setdefault("top_n", 8)
        parsed.setdefault("target_customer_name", None)
        parsed.setdefault("target_customer_name_2", None)
        parsed.setdefault("requested_tone", None)
        parsed.setdefault("days_since_enquiry", None)

        # Post-validate: fix common LLM misclassifications
        # regenerate_message with no named customer → find_leads
        if parsed["intent"] == "regenerate_message" and not parsed.get("target_customer_name"):
            parsed["intent"] = "find_leads"

        # regenerate_message with hallucinated name for a bulk query → find_leads
        if parsed["intent"] == "regenerate_message" and parsed.get("target_customer_name"):
            q_lower = query.lower()
            if re.search(r'\b(find|show|list|get|all|high.value)\b.*\bcustomers?\b', q_lower) or \
               re.search(r'\bcustomers?\b.*\b(likely|likely to|convert|generate|whatsapp)\b', q_lower):
                parsed["intent"] = "find_leads"
                parsed["target_customer_name"] = None

        # Detect LLM confusing credit score value with income (e.g. sets min_income=800 when
        # query says "credit score above 800 and income above 500000")
        if parsed.get("min_credit_score") is not None and parsed.get("min_income") is not None:
            cs = float(parsed["min_credit_score"])
            inc = float(parsed["min_income"])
            if abs(inc - cs) < 1 and 300 <= inc <= 900:
                income_re = re.search(
                    r'income\s+(?:above|over|more\s+than|at\s+least|exceeding)\s*[₹rs.]?\s*([\d,]+)',
                    query, re.IGNORECASE,
                )
                parsed["min_income"] = float(income_re.group(1).replace(",", "")) if income_re else None

        return parsed

    except Exception as e:
        logger.warning("[NODE: understand_intent] LLM parse failed (%s), using regex fallback", str(e)[:80])
        return _parse_regex(query)


def _parse_regex(query: str) -> Dict[str, Any]:
    """Regex-based fallback parser."""
    q = query.lower()

    result: Dict[str, Any] = {
        "intent": "find_leads",
        "city": None,
        "min_income": None,
        "max_income": None,
        "min_credit_score": None,
        "max_credit_score": None,
        "occupation": None,
        "days_since_enquiry": None,
        "top_n": 8,
        "target_customer_name": None,
        "target_customer_name_2": None,
        "requested_tone": None,
    }

    # --- Greeting detection (highest priority) ---
    if re.match(r'^(hi|hello|hey|howdy|greetings?|good\s+(?:morning|afternoon|evening|day))[\s!\.,]*$', q.strip()):
        result["intent"] = "greeting"
        return result

    # --- Aggregate summary ---
    if re.search(r'\b(summary|breakdown|how many|statistics|stats|all leads|priority leads|high.*medium.*low|tiers?)\b', q):
        result["intent"] = "aggregate_summary"
        return result

    # --- Compare customers ---
    compare_m = re.search(
        r'compare\s+([A-Za-z]+ [A-Za-z]+)\s+(?:and|vs\.?|versus|with)\s+([A-Za-z]+ [A-Za-z]+)',
        query, re.IGNORECASE
    )
    if not compare_m:
        compare_m = re.search(
            r'([A-Za-z]+ [A-Za-z]+)\s+(?:vs\.?|versus)\s+([A-Za-z]+ [A-Za-z]+)',
            query, re.IGNORECASE
        )
    if compare_m:
        result["intent"] = "compare_customers"
        result["target_customer_name"] = compare_m.group(1).strip().title()
        result["target_customer_name_2"] = compare_m.group(2).strip().title()
        return result

    # --- Single-customer intents (highest priority — check before generic patterns) ---
    # "regenerate * for [Name]" / "message for [Name]" / "generate * for [Name]"
    regen_patterns = [
        r"(?:regenerate|rewrite|create|send|generate)\s+(?:\w+\s+)*(?:message|whatsapp|msg)\s+for\s+([A-Za-z]+ [A-Za-z]+)",
        r"(?:message|whatsapp)\s+for\s+([A-Za-z]+ [A-Za-z]+)",
        r"([A-Za-z]+ [A-Za-z]+)\s*'?s?\s+(?:message|whatsapp)",
    ]
    for pat in regen_patterns:
        m = re.search(pat, q, re.IGNORECASE)
        if m:
            result["intent"] = "regenerate_message"
            result["target_customer_name"] = m.group(1).strip().title()
            break

    # "why is [Name]" / "tell me about [Name]" / "explain [Name]"
    if result["intent"] == "find_leads":
        explain_patterns = [
            r"why\s+is\s+([A-Za-z]+ [A-Za-z]+)",
            r"tell me about\s+([A-Za-z]+ [A-Za-z]+)",
            r"explain\s+([A-Za-z]+ [A-Za-z]+)",
            r"profile\s+(?:of|for)\s+([A-Za-z]+ [A-Za-z]+)",
            r"analyse\s+([A-Za-z]+ [A-Za-z]+)",
            r"analyze\s+([A-Za-z]+ [A-Za-z]+)",
            r"why\s+(?:is\s+)?([A-Za-z]+ [A-Za-z]+)\s+(?:a\s+)?(?:good|bad|top)",
        ]
        for pat in explain_patterns:
            m = re.search(pat, q, re.IGNORECASE)
            if m:
                result["intent"] = "explain_customer"
                result["target_customer_name"] = m.group(1).strip().title()
                break

    # --- Tone extraction ---
    for tone in ["urgent", "casual", "formal"]:
        if tone in q:
            result["requested_tone"] = tone
            break

    # --- If still find_leads, check for remaining intents ---
    if result["intent"] == "find_leads":
        city_map = {
            "mumbai": "Mumbai", "bombay": "Mumbai",
            "delhi": "Delhi", "new delhi": "Delhi",
            "bangalore": "Bangalore", "bengaluru": "Bangalore",
            "pune": "Pune", "hyderabad": "Hyderabad",
            "chennai": "Chennai", "kolkata": "Kolkata",
        }
        for key, val in city_map.items():
            if key in q:
                result["city"] = val
                result["intent"] = "filtered_search"
                break

        if re.search(r"self[- ]employed|self employment|business owner|entrepreneur|freelancer", q):
            result["occupation"] = "SELF_EMPLOYED"
            result["intent"] = "filtered_search"
        elif "salaried" in q:
            result["occupation"] = "SALARIED"
            result["intent"] = "filtered_search"

        income_m = re.search(
            r"(?:earning|income|salary|earn)\b[^\d₹]*(?:above|over|more\s+than|at\s+least|exceeding)?\s*[₹rs.]?\s*(\d[\d,]*(?:\.\d+)?)\s*(lakh|l\b)?"
            r"|[₹]\s*(\d[\d,]*(?:\.\d+)?)\s*(lakh|l\b)?",
            q, re.IGNORECASE,
        )
        if income_m:
            g1 = income_m.group(1) or income_m.group(3) or "0"
            g2 = income_m.group(2) or income_m.group(4)
            val = float(g1.replace(",", ""))
            if g2:
                val *= 100_000
            result["min_income"] = val
            result["intent"] = "filtered_search"

        credit_m = re.search(r"credit\s*(?:score)?\s*(?:above|over|>|≥|at\s+least)?\s*(\d{3})", q)
        if credit_m:
            result["min_credit_score"] = int(credit_m.group(1))
            result["intent"] = "filtered_search"

        # Days since enquiry: "last X days", "past X days", "within X days"
        days_m = re.search(r"(?:last|past|within|in\s+the\s+last)\s+(\d+)\s+days?", q)
        if days_m:
            result["days_since_enquiry"] = int(days_m.group(1))
            result["intent"] = "filtered_search"

    # --- Top-N ---
    n_m = re.search(r"\btop\s+(\d+)\b", q)
    if n_m:
        result["top_n"] = int(n_m.group(1))

    return result
