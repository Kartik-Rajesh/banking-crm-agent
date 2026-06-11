"""Unit tests for the scoring engine — no LLM dependency."""

import pytest
from datetime import datetime, timedelta

from backend.tools.scoring_tools import (
    score_customer,
    recommend_product,
    score_and_recommend_customers,
    _compute_income_stability,
    _compute_credit_score_subscore,
    _compute_dti_subscore,
    _compute_balance_subscore,
    _compute_transaction_regularity,
    _compute_enquiry_recency,
    SCORING_WEIGHTS,
)


# ── Fixtures ────────────────────────────────────────────────────────────────

def make_customer(**overrides):
    base = {
        "id": 1,
        "name": "Test Customer",
        "occupation": "SALARIED",
        "monthly_income": 100000,
        "credit_score": 750,
        "account_balance": 200000,
        "existing_loans": [],
        "city": "Mumbai",
        "age": 35,
        "risk_profile": "LOW",
    }
    base.update(overrides)
    return base


def make_salary_transactions(count: int, days_back_start: int = 5) -> list:
    """Generate salary credit transactions in the last 90 days."""
    transactions = []
    for i in range(count):
        date = datetime.now() - timedelta(days=days_back_start + i * 30)
        transactions.append(
            {
                "transaction_type": "SALARY",
                "transaction_date": date.isoformat(),
                "amount": 100000,
                "category": "INCOME",
            }
        )
    return transactions


def make_recent_enquiry(days_ago: int) -> list:
    return [
        {
            "enquiry_date": (datetime.now() - timedelta(days=days_ago)).isoformat(),
            "product_type": "PERSONAL_LOAN",
            "status": "PENDING",
        }
    ]


# ── Sub-score unit tests ─────────────────────────────────────────────────────

class TestIncomeStability:
    def test_three_salary_credits_salaried(self):
        transactions = make_salary_transactions(3)
        score = _compute_income_stability(transactions, "SALARIED")
        assert score == 1.0

    def test_two_salary_credits(self):
        transactions = make_salary_transactions(2)
        score = _compute_income_stability(transactions, "SALARIED")
        assert abs(score - 2/3) < 0.01

    def test_no_salary_credits(self):
        score = _compute_income_stability([], "SALARIED")
        assert score == 0.0

    def test_old_transactions_not_counted(self):
        """Transactions older than 90 days shouldn't count."""
        old_txn = [{
            "transaction_type": "SALARY",
            "transaction_date": (datetime.now() - timedelta(days=120)).isoformat(),
            "amount": 100000,
        }]
        score = _compute_income_stability(old_txn, "SALARIED")
        assert score == 0.0

    def test_self_employed_different_logic(self):
        """Self-employed uses credit transaction count, not SALARY type."""
        score = _compute_income_stability([], "SELF_EMPLOYED")
        assert score == 0.0


class TestCreditScoreSubscore:
    def test_max_score(self):
        # 850 → (850-300)/550 = 1.0
        assert _compute_credit_score_subscore(850) == pytest.approx(1.0)

    def test_min_clamp(self):
        # Score below 300 → 0
        assert _compute_credit_score_subscore(250) == 0.0

    def test_typical_score(self):
        # 750 → (750-300)/550 ≈ 0.818
        assert _compute_credit_score_subscore(750) == pytest.approx(450 / 550, rel=0.01)

    def test_boundary_300(self):
        assert _compute_credit_score_subscore(300) == 0.0


class TestDTISubscore:
    def test_no_loans(self):
        assert _compute_dti_subscore([], 100000) == 1.0

    def test_50_percent_dti(self):
        loans = [{"emi": 50000, "outstanding": 500000}]
        score = _compute_dti_subscore(loans, 100000)
        assert score == pytest.approx(0.5)

    def test_over_100_percent_dti_clamps_to_zero(self):
        loans = [{"emi": 120000, "outstanding": 1000000}]
        score = _compute_dti_subscore(loans, 100000)
        assert score == 0.0

    def test_zero_income_returns_zero(self):
        assert _compute_dti_subscore([], 0) == 0.0


class TestBalanceSubscore:
    def test_three_months_buffer(self):
        # balance = 3 * income → score = 1.0
        assert _compute_balance_subscore(300000, 100000) == pytest.approx(1.0)

    def test_low_balance(self):
        # balance = 0.5 * income → score = 0.5/3 ≈ 0.167
        assert _compute_balance_subscore(50000, 100000) == pytest.approx(50000 / 300000, rel=0.01)

    def test_caps_at_one(self):
        assert _compute_balance_subscore(1000000, 100000) == 1.0


class TestTransactionRegularity:
    def test_active_account(self):
        transactions = [
            {
                "transaction_date": (datetime.now() - timedelta(days=i * 3)).isoformat(),
                "transaction_type": "DEBIT",
            }
            for i in range(30)
        ]
        score = _compute_transaction_regularity(transactions)
        assert score == 1.0  # Clipped at 1.0

    def test_inactive_account(self):
        old_transactions = [
            {
                "transaction_date": (datetime.now() - timedelta(days=200)).isoformat(),
                "transaction_type": "DEBIT",
            }
        ]
        score = _compute_transaction_regularity(old_transactions)
        assert score == 0.0


class TestEnquiryRecency:
    def test_recent_enquiry_30d(self):
        enquiries = make_recent_enquiry(10)
        assert _compute_enquiry_recency(enquiries) == 1.0

    def test_enquiry_between_30_90d(self):
        enquiries = make_recent_enquiry(60)
        assert _compute_enquiry_recency(enquiries) == 0.5

    def test_old_enquiry(self):
        enquiries = make_recent_enquiry(120)
        assert _compute_enquiry_recency(enquiries) == 0.0

    def test_no_enquiry(self):
        assert _compute_enquiry_recency([]) == 0.0


# ── Integration: full score_customer ────────────────────────────────────────

class TestScoreCustomer:
    def test_prime_customer_scores_high(self):
        customer = make_customer(
            monthly_income=150000,
            credit_score=800,
            account_balance=500000,
            existing_loans=[],
        )
        transactions = make_salary_transactions(3)
        enquiries = make_recent_enquiry(15)

        result = score_customer(customer, transactions, enquiries)

        assert result["conversion_score"] > 70
        assert "score_breakdown" in result
        assert "score_reasoning" in result
        assert 0 <= result["conversion_probability"] <= 100

    def test_poor_profile_scores_low(self):
        customer = make_customer(
            monthly_income=30000,
            credit_score=610,
            account_balance=10000,
            existing_loans=[{"emi": 20000, "outstanding": 300000}],
        )
        result = score_customer(customer, [], [])
        assert result["conversion_score"] < 50

    def test_score_breakdown_has_all_factors(self):
        customer = make_customer()
        result = score_customer(customer, [], [])
        breakdown = result["score_breakdown"]
        for factor in SCORING_WEIGHTS:
            assert factor in breakdown, f"Missing factor: {factor}"

    def test_score_is_bounded(self):
        customer = make_customer(
            monthly_income=500000,
            credit_score=850,
            account_balance=2000000,
        )
        result = score_customer(customer, make_salary_transactions(3), make_recent_enquiry(5))
        assert 0 <= result["conversion_score"] <= 100

    def test_reasoning_is_non_empty(self):
        customer = make_customer()
        result = score_customer(customer, make_salary_transactions(2), [])
        assert len(result["score_reasoning"]) > 10


# ── Product recommendation ───────────────────────────────────────────────────

class TestRecommendProduct:
    def test_premium_salaried(self):
        customer = make_customer(
            occupation="SALARIED",
            monthly_income=80000,
            credit_score=750,
            existing_loans=[],
        )
        product = recommend_product(customer)
        assert product is not None
        assert "Premium" in product["name"]

    def test_standard_salaried_lower_credit(self):
        customer = make_customer(
            occupation="SALARIED",
            monthly_income=30000,
            credit_score=660,
            existing_loans=[],
        )
        product = recommend_product(customer)
        assert product is not None
        assert "Standard" in product["name"]

    def test_topup_for_existing_loan_holder(self):
        customer = make_customer(
            credit_score=720,
            existing_loans=[{"type": "HOME_LOAN", "emi": 25000, "outstanding": 2000000}],
        )
        product = recommend_product(customer)
        assert product is not None
        assert "Top-Up" in product["name"]

    def test_self_employed_product(self):
        customer = make_customer(
            occupation="SELF_EMPLOYED",
            monthly_income=100000,
            credit_score=700,
            existing_loans=[],
        )
        product = recommend_product(customer)
        assert product is not None
        assert "Self Employed" in product["name"]

    def test_very_low_credit_no_product(self):
        customer = make_customer(
            occupation="SALARIED",
            monthly_income=20000,
            credit_score=600,
            existing_loans=[],
        )
        product = recommend_product(customer)
        assert product is None


# ── Batch scoring ────────────────────────────────────────────────────────────

class TestBatchScoring:
    def test_sorted_by_score_descending(self):
        customers = [
            make_customer(id=1, credit_score=800, monthly_income=150000),
            make_customer(id=2, credit_score=620, monthly_income=30000),
            make_customer(id=3, credit_score=730, monthly_income=80000),
        ]
        results = score_and_recommend_customers(
            customers=customers,
            transactions_by_customer={1: make_salary_transactions(3), 2: [], 3: make_salary_transactions(2)},
            enquiries_by_customer={1: make_recent_enquiry(10), 2: [], 3: []},
        )
        scores = [r["conversion_score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_all_customers_scored(self):
        customers = [make_customer(id=i) for i in range(1, 6)]
        results = score_and_recommend_customers(
            customers=customers,
            transactions_by_customer={},
            enquiries_by_customer={},
        )
        assert len(results) == 5
        for r in results:
            assert "conversion_score" in r
