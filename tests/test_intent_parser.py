"""Unit tests for the intent parser — validates regex pre-checks and LLM fallback behaviour."""

import pytest
from backend.agents.nodes.query_understanding import _pre_check_patterns, _parse_regex


class TestPreCheckPatterns:
    """Tests for the fast deterministic pre-check layer."""

    # ── Greetings ────────────────────────────────────────────────────────────

    def test_greeting_hi(self):
        result = _pre_check_patterns("hi")
        assert result is not None
        assert result["intent"] == "greeting"

    def test_greeting_hello(self):
        result = _pre_check_patterns("Hello!")
        assert result is not None
        assert result["intent"] == "greeting"

    def test_greeting_good_morning(self):
        result = _pre_check_patterns("Good morning")
        assert result is not None
        assert result["intent"] == "greeting"

    def test_non_greeting_returns_none(self):
        result = _pre_check_patterns("Find high-value customers")
        assert result is None

    # ── Compare customers ────────────────────────────────────────────────────

    def test_compare_with_keyword(self):
        result = _pre_check_patterns("Compare Arjun Reddy and Tarun Walia")
        assert result is not None
        assert result["intent"] == "compare_customers"
        assert result["target_customer_name"] == "Arjun Reddy"
        assert result["target_customer_name_2"] == "Tarun Walia"

    def test_compare_vs_format(self):
        result = _pre_check_patterns("Arjun Reddy vs Tarun Walia")
        assert result is not None
        assert result["intent"] == "compare_customers"

    def test_compare_versus_format(self):
        result = _pre_check_patterns("Arjun Reddy versus Tarun Walia — who to approach first?")
        assert result is not None
        assert result["intent"] == "compare_customers"

    # ── Aggregate summary ────────────────────────────────────────────────────

    def test_aggregate_how_many(self):
        result = _pre_check_patterns("How many high-value leads do I have?")
        assert result is not None
        assert result["intent"] == "aggregate_summary"

    def test_aggregate_breakdown(self):
        result = _pre_check_patterns("Give me a full breakdown of the lead pipeline")
        assert result is not None
        assert result["intent"] == "aggregate_summary"

    def test_aggregate_priority_tiers(self):
        result = _pre_check_patterns("Show high medium low priority leads")
        assert result is not None
        assert result["intent"] == "aggregate_summary"

    # ── Regenerate message ───────────────────────────────────────────────────

    def test_regenerate_single_customer(self):
        result = _pre_check_patterns("Regenerate WhatsApp message for Arjun Reddy")
        assert result is not None
        assert result["intent"] == "regenerate_message"
        assert result["target_customer_name"] == "Arjun Reddy"

    def test_regenerate_with_tone(self):
        result = _pre_check_patterns("Regenerate message for Arjun Reddy in urgent tone")
        assert result is not None
        assert result["intent"] == "regenerate_message"
        assert result["requested_tone"] == "urgent"

    # ── Bulk generate — should be find_leads, not regenerate_message ─────────

    def test_bulk_generate_is_find_leads(self):
        result = _pre_check_patterns("Find customers and generate WhatsApp messages")
        assert result is not None
        assert result["intent"] == "find_leads"

    def test_top_n_generate_is_find_leads(self):
        result = _pre_check_patterns("Generate messages for top 5 customers")
        assert result is not None
        assert result["intent"] == "find_leads"
        assert result["top_n"] == 5


class TestRegexFallback:
    """Tests for the regex fallback parser."""

    # ── Basic intents ────────────────────────────────────────────────────────

    def test_default_find_leads(self):
        result = _parse_regex("Find high-value loan candidates")
        assert result["intent"] == "find_leads"

    def test_city_filter_switches_to_filtered_search(self):
        result = _parse_regex("Show me customers in Mumbai")
        assert result["intent"] == "filtered_search"
        assert result["city"] == "Mumbai"

    def test_bombay_alias(self):
        result = _parse_regex("Customers in Bombay")
        assert result["city"] == "Mumbai"

    def test_bengaluru_alias(self):
        result = _parse_regex("Show leads in Bengaluru")
        assert result["city"] == "Bangalore"

    # ── Occupation filters ───────────────────────────────────────────────────

    def test_salaried_filter(self):
        result = _parse_regex("Show salaried customers")
        assert result["occupation"] == "SALARIED"
        assert result["intent"] == "filtered_search"

    def test_self_employed_filter(self):
        result = _parse_regex("Find self-employed customers")
        assert result["occupation"] == "SELF_EMPLOYED"

    def test_business_owner_alias(self):
        result = _parse_regex("Show business owners with good credit")
        assert result["occupation"] == "SELF_EMPLOYED"

    # ── Credit score filters ─────────────────────────────────────────────────

    def test_credit_score_above(self):
        result = _parse_regex("Customers with credit score above 750")
        assert result["min_credit_score"] == 750

    def test_credit_score_over(self):
        result = _parse_regex("credit score over 720")
        assert result["min_credit_score"] == 720

    # ── Top-N extraction ─────────────────────────────────────────────────────

    def test_top_n_extraction(self):
        result = _parse_regex("Find top 10 loan candidates")
        assert result["top_n"] == 10

    def test_top_n_default(self):
        result = _parse_regex("Find loan candidates")
        assert result["top_n"] == 8

    # ── Days since enquiry ───────────────────────────────────────────────────

    def test_days_since_enquiry(self):
        result = _parse_regex("Customers who enquired in the last 30 days")
        assert result["days_since_enquiry"] == 30
        assert result["intent"] == "filtered_search"

    # ── Single-customer intents ──────────────────────────────────────────────

    def test_explain_customer_why(self):
        result = _parse_regex("Why is Arjun Reddy a good candidate?")
        assert result["intent"] == "explain_customer"
        assert result["target_customer_name"] == "Arjun Reddy"

    def test_explain_tell_me_about(self):
        result = _parse_regex("Tell me about Tarun Walia")
        assert result["intent"] == "explain_customer"
        assert result["target_customer_name"] == "Tarun Walia"

    def test_regenerate_message_for_customer(self):
        result = _parse_regex("Generate a WhatsApp message for Arjun Reddy")
        assert result["intent"] == "regenerate_message"
        assert result["target_customer_name"] == "Arjun Reddy"

    # ── Tone extraction ──────────────────────────────────────────────────────

    def test_urgent_tone_extracted(self):
        result = _parse_regex("Send an urgent message to Arjun Reddy")
        assert result["requested_tone"] == "urgent"

    def test_formal_tone_extracted(self):
        result = _parse_regex("Write a formal message for Tarun Walia")
        assert result["requested_tone"] == "formal"

    def test_casual_tone_extracted(self):
        result = _parse_regex("Generate a casual WhatsApp for Arjun Reddy")
        assert result["requested_tone"] == "casual"

    # ── Aggregate summary ────────────────────────────────────────────────────

    def test_aggregate_summary_keyword(self):
        result = _parse_regex("Give me a summary of all leads")
        assert result["intent"] == "aggregate_summary"

    def test_aggregate_breakdown_keyword(self):
        result = _parse_regex("Show me the lead breakdown by priority")
        assert result["intent"] == "aggregate_summary"

    # ── Compare customers ────────────────────────────────────────────────────

    def test_compare_two_customers(self):
        result = _parse_regex("Compare Arjun Reddy and Tarun Walia")
        assert result["intent"] == "compare_customers"
        assert result["target_customer_name"] == "Arjun Reddy"
        assert result["target_customer_name_2"] == "Tarun Walia"
