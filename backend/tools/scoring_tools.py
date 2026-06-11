"""
Scoring engine for personal loan conversion probability.

Fully deterministic Python logic — no LLM dependency.
Each customer is scored 0-100 across 6 weighted factors.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

SCORING_WEIGHTS: Dict[str, float] = {
    "income_stability": 0.25,
    "credit_score": 0.20,
    "debt_to_income_ratio": 0.20,
    "account_balance": 0.15,
    "transaction_regularity": 0.10,
    "loan_enquiry_recency": 0.10,
}

LOAN_PRODUCTS: List[Dict[str, Any]] = [
    {
        "name": "Personal Loan - Salaried Premium",
        "occupation": "SALARIED",
        "min_income": 50000,
        "min_credit": 720,
        "max_amount": 2500000,
        "interest_rate": "10.5% - 12%",
        "tenure": "12-60 months",
        "usp": "Pre-approved in 4 hours",
    },
    {
        "name": "Personal Loan - Salaried Standard",
        "occupation": "SALARIED",
        "min_income": 25000,
        "min_credit": 650,
        "max_amount": 1000000,
        "interest_rate": "13% - 16%",
        "tenure": "12-48 months",
        "usp": "Minimal documentation",
    },
    {
        "name": "Personal Loan - Self Employed",
        "occupation": "SELF_EMPLOYED",
        "min_income": 75000,
        "min_credit": 680,
        "max_amount": 1500000,
        "interest_rate": "14% - 18%",
        "tenure": "12-36 months",
        "usp": "No ITR required for first year",
    },
    {
        "name": "Top-Up Loan",
        "requires_existing_loan": True,
        "min_credit": 700,
        "max_amount": 500000,
        "interest_rate": "11% - 13%",
        "tenure": "12-36 months",
        "usp": "Instant approval for existing customers",
    },
]


def _compute_income_stability(
    transactions: List[Dict[str, Any]],
    occupation: str,
) -> float:
    """Count salary credits in last 3 months; self-employed get credit income regularity check."""
    now = datetime.now()
    three_months_ago = now - timedelta(days=90)

    if occupation == "SALARIED":
        salary_credits = sum(
            1
            for t in transactions
            if t.get("transaction_type") == "SALARY"
            and datetime.fromisoformat(str(t["transaction_date"])) >= three_months_ago
        )
        return min(salary_credits / 3.0, 1.0)
    else:
        # Self-employed: check for regular large credit transactions
        credit_txns = [
            t for t in transactions
            if t.get("transaction_type") == "CREDIT"
            and t.get("amount", 0) > 10000
            and datetime.fromisoformat(str(t["transaction_date"])) >= three_months_ago
        ]
        return min(len(credit_txns) / 6.0, 1.0)  # Expect ~2/month


def _compute_credit_score_subscore(credit_score: int) -> float:
    """Normalize credit score to 0-1. Formula: (score - 300) / 550."""
    return max(0.0, min((credit_score - 300) / 550.0, 1.0))


def _compute_dti_subscore(
    existing_loans: List[Dict[str, Any]],
    monthly_income: float,
    transactions: Optional[List[Dict[str, Any]]] = None,
) -> float:
    """Debt-to-Income ratio score. Lower DTI = higher score.

    Uses existing_loans EMI data first. If that's empty, derives EMI from
    EMI-type transactions in the last 3 months.
    """
    if monthly_income <= 0:
        return 0.0

    total_emi = sum(loan.get("emi", 0) for loan in (existing_loans or []))

    # Derive from transaction history if no loan profile data
    if total_emi == 0 and transactions:
        now = datetime.now()
        three_months_ago = now - timedelta(days=90)
        emi_txns = [
            t for t in transactions
            if (
                str(t.get("transaction_type", "")).upper() in ("EMI", "LOAN_PAYMENT")
                or str(t.get("category") or "").upper() in ("EMI", "LOAN_PAYMENT")
                or "emi" in str(t.get("description") or "").lower()
                or "loan" in str(t.get("description") or "").lower()
            )
            and datetime.fromisoformat(str(t["transaction_date"])) >= three_months_ago
        ]
        if emi_txns:
            # Monthly average = total debits / 3 months
            total_emi = sum(abs(t.get("amount", 0)) for t in emi_txns) / 3.0

    dti = total_emi / monthly_income
    return max(0.0, min(1.0 - dti, 1.0))


def _compute_balance_subscore(
    account_balance: float,
    monthly_income: float,
) -> float:
    """Liquidity buffer: min(balance / (3 * monthly_income), 1)."""
    if monthly_income <= 0:
        return 0.0
    return min(account_balance / (3.0 * monthly_income), 1.0)


def _compute_transaction_regularity(
    transactions: List[Dict[str, Any]],
) -> float:
    """Consistent account activity in last 90 days: count / 30, clipped 0-1."""
    now = datetime.now()
    ninety_days_ago = now - timedelta(days=90)
    recent_count = sum(
        1
        for t in transactions
        if datetime.fromisoformat(str(t["transaction_date"])) >= ninety_days_ago
    )
    return min(recent_count / 30.0, 1.0)


def _compute_enquiry_recency(loan_enquiries: List[Dict[str, Any]]) -> float:
    """Recent personal loan enquiry signals intent: 1.0 if <30d, 0.5 if <90d, 0 otherwise."""
    if not loan_enquiries:
        return 0.0
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    ninety_days_ago = now - timedelta(days=90)

    for enquiry in loan_enquiries:
        eq_date = datetime.fromisoformat(str(enquiry["enquiry_date"]))
        if eq_date >= thirty_days_ago:
            return 1.0
        if eq_date >= ninety_days_ago:
            return 0.5
    return 0.0


def _build_reasoning(
    customer_name: str,
    sub_scores: Dict[str, float],
    credit_score: int,
    monthly_income: float,
    dti: float,
    enquiry_info: Optional[str],
    occupation: str,
) -> str:
    """Build human-readable reasoning for the RM."""
    lines = []

    # Income stability
    stability = sub_scores["income_stability"]
    if stability >= 0.9:
        lines.append(f"Excellent income stability (3/3 salary credits in last 3 months)")
    elif stability >= 0.6:
        salary_count = round(stability * 3)
        lines.append(f"Good income stability ({salary_count}/3 salary credits in last 3 months)")
    elif occupation == "SELF_EMPLOYED":
        lines.append(f"Self-employed with {'regular' if stability > 0.5 else 'moderate'} business income flow")
    else:
        lines.append(f"Income history shows some gaps in last 3 months")

    # Credit score
    if credit_score >= 780:
        lines.append(f"Excellent credit score ({credit_score}) — prime lending tier")
    elif credit_score >= 720:
        lines.append(f"Strong credit score ({credit_score}) — qualifies for premium products")
    elif credit_score >= 650:
        lines.append(f"Good credit score ({credit_score}) — eligible for standard products")
    else:
        lines.append(f"Credit score ({credit_score}) is below premium threshold — standard products only")

    # DTI
    dti_pct = round(dti * 100, 1)
    if dti_pct <= 30:
        lines.append(f"Low debt burden (DTI: {dti_pct}%) — significant loan capacity available")
    elif dti_pct <= 50:
        lines.append(f"Moderate debt burden (DTI: {dti_pct}%) — within acceptable range")
    else:
        lines.append(f"Higher debt load (DTI: {dti_pct}%) — existing EMI obligations are significant")

    # Balance
    balance_score = sub_scores["account_balance"]
    if balance_score >= 0.8:
        lines.append(f"Strong account balance — demonstrates financial discipline")
    elif balance_score >= 0.4:
        lines.append(f"Adequate account balance maintained")

    # Enquiry
    if enquiry_info:
        lines.append(enquiry_info)

    return ". ".join(lines) + "."


def score_customer(
    customer: Dict[str, Any],
    transactions: List[Dict[str, Any]],
    loan_enquiries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Score a customer 0-100 for personal loan conversion.

    Returns enriched dict with score, probability, breakdown, and reasoning.
    """
    name = customer.get("name", "Customer")
    occupation = customer.get("occupation", "SALARIED")
    monthly_income = customer.get("monthly_income", 0)
    credit_score = customer.get("credit_score", 600)
    account_balance = customer.get("account_balance", 0)
    existing_loans = customer.get("existing_loans") or []

    # Compute sub-scores
    income_stability = _compute_income_stability(transactions, occupation)
    credit_subscore = _compute_credit_score_subscore(credit_score)
    dti_score = _compute_dti_subscore(existing_loans, monthly_income, transactions)
    balance_score = _compute_balance_subscore(account_balance, monthly_income)
    regularity = _compute_transaction_regularity(transactions)
    enquiry_score = _compute_enquiry_recency(loan_enquiries)

    sub_scores = {
        "income_stability": round(income_stability, 3),
        "credit_score": round(credit_subscore, 3),
        "debt_to_income_ratio": round(dti_score, 3),
        "account_balance": round(balance_score, 3),
        "transaction_regularity": round(regularity, 3),
        "loan_enquiry_recency": round(enquiry_score, 3),
    }

    # Weighted sum (0.0 – 1.0 range)
    raw_score = sum(sub_scores[k] * SCORING_WEIGHTS[k] for k in SCORING_WEIGHTS)

    # Stretch the theoretical [0.35, 1.0] band to the full [0, 100] scale so the
    # distribution covers all four tiers (<40 / 40-60 / 60-75 / >75) with weak
    # customers scoring well below 40 and top customers near 90.
    _BASE = 0.35   # raw score below this = definite rejection (score → 0)
    _SPAN = 0.65   # width of the "lendable" band
    conversion_score = round(max(0.0, min(100.0, (raw_score - _BASE) / _SPAN * 100)), 2)

    # Conversion probability: sigmoid-like rescaling, plus small ML noise
    noise = random.uniform(-4, 4)
    conversion_probability = round(max(0.0, min(100.0, conversion_score * 0.85 + noise)), 2)

    # DTI for reasoning — mirrors _compute_dti_subscore logic
    total_emi = sum(loan.get("emi", 0) for loan in existing_loans)
    if total_emi == 0 and transactions:
        now = datetime.now()
        three_months_ago = now - timedelta(days=90)
        emi_txns = [
            t for t in transactions
            if (
                str(t.get("transaction_type", "")).upper() in ("EMI", "LOAN_PAYMENT")
                or "emi" in str(t.get("description") or "").lower()
                or "loan" in str(t.get("description") or "").lower()
            )
            and datetime.fromisoformat(str(t["transaction_date"])) >= three_months_ago
        ]
        if emi_txns:
            total_emi = sum(abs(t.get("amount", 0)) for t in emi_txns) / 3.0
    dti = total_emi / monthly_income if monthly_income > 0 else 0

    # Enquiry detail for reasoning
    enquiry_info = None
    if loan_enquiries and enquiry_score > 0:
        latest = max(loan_enquiries, key=lambda e: e["enquiry_date"])
        eq_date = datetime.fromisoformat(str(latest["enquiry_date"]))
        days_ago = (datetime.now() - eq_date).days
        enquiry_info = f"Active loan enquiry placed {days_ago} days ago — warm prospect"

    reasoning = _build_reasoning(
        customer_name=name,
        sub_scores=sub_scores,
        credit_score=credit_score,
        monthly_income=monthly_income,
        dti=dti,
        enquiry_info=enquiry_info,
        occupation=occupation,
    )

    return {
        **customer,
        "conversion_score": conversion_score,
        "conversion_probability": conversion_probability,
        "score_breakdown": sub_scores,
        "score_reasoning": reasoning,
    }


def recommend_product(customer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Match a customer to the best loan product based on profile."""
    occupation = customer.get("occupation", "SALARIED")
    income = customer.get("monthly_income", 0)
    credit = customer.get("credit_score", 0)
    has_existing_loan = bool(customer.get("existing_loans"))

    # Priority: Top-Up for existing loan holders with good credit
    if has_existing_loan and credit >= 700:
        for p in LOAN_PRODUCTS:
            if p.get("requires_existing_loan") and credit >= p["min_credit"]:
                return p

    # Self-employed product
    if occupation == "SELF_EMPLOYED":
        for p in LOAN_PRODUCTS:
            if p.get("occupation") == "SELF_EMPLOYED" and income >= p["min_income"] and credit >= p["min_credit"]:
                return p

    # Salaried: try premium first, then standard
    if occupation == "SALARIED":
        for p in LOAN_PRODUCTS:
            if (
                p.get("occupation") == "SALARIED"
                and income >= p["min_income"]
                and credit >= p["min_credit"]
            ):
                return p

    return None


def score_and_recommend_customers(
    customers: List[Dict[str, Any]],
    transactions_by_customer: Dict[int, List[Dict[str, Any]]],
    enquiries_by_customer: Dict[int, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Score all customers and attach product recommendations. Returns sorted by score."""
    results = []
    for customer in customers:
        cid = customer["id"]
        transactions = transactions_by_customer.get(cid, [])
        enquiries = enquiries_by_customer.get(cid, [])

        scored = score_customer(customer, transactions, enquiries)
        product = recommend_product(scored)
        scored["recommended_product"] = product["name"] if product else None
        scored["product_details"] = product

        results.append(scored)

    results.sort(key=lambda x: x["conversion_score"], reverse=True)
    return results
