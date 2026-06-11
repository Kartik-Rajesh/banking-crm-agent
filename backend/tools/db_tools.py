"""LangChain-compatible tools for querying the banking CRM database."""

from __future__ import annotations

import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.database.models import Customer, Transaction, LoanEnquiry
from backend.database.connection import SessionLocal

logger = logging.getLogger(__name__)


def _customer_to_dict(customer: Customer) -> Dict[str, Any]:
    """Serialize a Customer ORM object to a plain dict."""
    return {
        "id": customer.id,
        "name": customer.name,
        "age": customer.age,
        "phone": customer.phone,
        "email": customer.email,
        "city": customer.city,
        "occupation": customer.occupation,
        "monthly_income": customer.monthly_income,
        "credit_score": customer.credit_score,
        "existing_loans": customer.existing_loans or [],
        "account_balance": customer.account_balance,
        "account_type": customer.account_type,
        "customer_since": str(customer.customer_since),
        "last_interaction_date": str(customer.last_interaction_date) if customer.last_interaction_date else None,
        "relationship_manager_id": customer.relationship_manager_id,
        "kyc_status": customer.kyc_status,
        "risk_profile": customer.risk_profile,
    }


def _transaction_to_dict(t: Transaction) -> Dict[str, Any]:
    return {
        "id": t.id,
        "customer_id": t.customer_id,
        "transaction_date": t.transaction_date.isoformat(),
        "amount": t.amount,
        "transaction_type": t.transaction_type,
        "category": t.category,
        "description": t.description,
        "merchant": t.merchant,
    }


def _enquiry_to_dict(e: LoanEnquiry) -> Dict[str, Any]:
    return {
        "id": e.id,
        "customer_id": e.customer_id,
        "enquiry_date": e.enquiry_date.isoformat(),
        "product_type": e.product_type,
        "amount_requested": e.amount_requested,
        "status": e.status,
    }


def get_customers_by_criteria(
    city: Optional[str] = None,
    min_income: Optional[float] = None,
    max_income: Optional[float] = None,
    min_credit_score: Optional[int] = None,
    max_credit_score: Optional[int] = None,
    occupation: Optional[str] = None,
    risk_profile: Optional[str] = None,
    days_since_enquiry: Optional[int] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """
    Query customers from DB with optional filters.

    Returns customers plus their recent transactions and loan enquiries.
    """
    db = SessionLocal()
    try:
        query = db.query(Customer)

        if city:
            query = query.filter(Customer.city.ilike(f"%{city}%"))
        if min_income:
            query = query.filter(Customer.monthly_income >= min_income)
        if max_income:
            query = query.filter(Customer.monthly_income <= max_income)
        if min_credit_score:
            query = query.filter(Customer.credit_score >= min_credit_score)
        if max_credit_score:
            query = query.filter(Customer.credit_score <= max_credit_score)
        if occupation:
            query = query.filter(Customer.occupation.ilike(f"%{occupation}%"))
        if risk_profile:
            query = query.filter(Customer.risk_profile == risk_profile.upper())
        if days_since_enquiry is not None:
            cutoff = datetime.utcnow() - timedelta(days=days_since_enquiry)
            query = (
                query.join(LoanEnquiry, Customer.id == LoanEnquiry.customer_id)
                .filter(LoanEnquiry.enquiry_date >= cutoff)
                .distinct()
            )

        customers = query.limit(limit).all()
        customer_dicts = [_customer_to_dict(c) for c in customers]

        # Fetch transactions + enquiries for each customer
        customer_ids = [c.id for c in customers]
        transactions_by_customer: Dict[int, List[Dict]] = {cid: [] for cid in customer_ids}
        enquiries_by_customer: Dict[int, List[Dict]] = {cid: [] for cid in customer_ids}

        if customer_ids:
            all_txns = db.query(Transaction).filter(Transaction.customer_id.in_(customer_ids)).all()
            for t in all_txns:
                transactions_by_customer[t.customer_id].append(_transaction_to_dict(t))

            all_enquiries = db.query(LoanEnquiry).filter(LoanEnquiry.customer_id.in_(customer_ids)).all()
            for e in all_enquiries:
                enquiries_by_customer[e.customer_id].append(_enquiry_to_dict(e))

        logger.info(
            "get_customers_by_criteria",
            extra={
                "filters": {
                    "city": city, "min_income": min_income,
                    "min_credit_score": min_credit_score, "occupation": occupation,
                },
                "result_count": len(customer_dicts),
            },
        )

        return {
            "customers": customer_dicts,
            "transactions_by_customer": transactions_by_customer,
            "enquiries_by_customer": enquiries_by_customer,
            "total": len(customer_dicts),
        }
    finally:
        db.close()


def get_customer_by_id(customer_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a single customer with full transaction and enquiry history."""
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return None

        transactions = db.query(Transaction).filter(Transaction.customer_id == customer_id).all()
        enquiries = db.query(LoanEnquiry).filter(LoanEnquiry.customer_id == customer_id).all()

        result = _customer_to_dict(customer)
        result["transactions"] = [_transaction_to_dict(t) for t in transactions]
        result["loan_enquiries"] = [_enquiry_to_dict(e) for e in enquiries]
        return result
    finally:
        db.close()


def get_customer_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Find a customer by partial name match."""
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.name.ilike(f"%{name}%")).first()
        if not customer:
            return None
        return get_customer_by_id(customer.id)
    finally:
        db.close()


def search_customers_by_name(name: str) -> List[Dict[str, Any]]:
    """Search customers by name, returns list of matches."""
    db = SessionLocal()
    try:
        customers = db.query(Customer).filter(Customer.name.ilike(f"%{name}%")).limit(5).all()
        return [_customer_to_dict(c) for c in customers]
    finally:
        db.close()
