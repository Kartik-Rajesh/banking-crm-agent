"""REST endpoints for customer data and scoring."""

from __future__ import annotations

import logging
from typing import Optional, List

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import Customer, Transaction, LoanEnquiry
from backend.tools.db_tools import (
    get_customers_by_criteria,
    get_customer_by_id,
    _customer_to_dict,
    _transaction_to_dict,
    _enquiry_to_dict,
)
from backend.tools.scoring_tools import score_customer, recommend_product

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("")
async def list_customers(
    city: Optional[str] = Query(None),
    min_income: Optional[float] = Query(None),
    min_credit_score: Optional[int] = Query(None),
    occupation: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, description="Minimum conversion score 0-100"),
    limit: int = Query(20, le=50),
    scored: bool = Query(True, description="Include conversion scores"),
):
    """
    List customers with optional filtering and scoring.

    Returns scored + product-recommended customer list by default.
    """
    try:
        result = get_customers_by_criteria(
            city=city,
            min_income=min_income,
            min_credit_score=min_credit_score,
            occupation=occupation,
            limit=limit,
        )

        customers = result["customers"]
        transactions_by = result["transactions_by_customer"]
        enquiries_by = result["enquiries_by_customer"]

        if scored:
            from backend.tools.scoring_tools import score_and_recommend_customers
            customers = score_and_recommend_customers(
                customers=customers,
                transactions_by_customer={int(k): v for k, v in transactions_by.items()},
                enquiries_by_customer={int(k): v for k, v in enquiries_by.items()},
            )

            if min_score is not None:
                customers = [c for c in customers if c.get("conversion_score", 0) >= min_score]

        return {
            "customers": customers,
            "total": len(customers),
        }

    except Exception as e:
        logger.error(f"List customers failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}")
async def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Get full customer profile with transaction history and scoring."""
    customer_data = get_customer_by_id(customer_id)
    if not customer_data:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    # Score the customer
    transactions = customer_data.get("transactions", [])
    enquiries = customer_data.get("loan_enquiries", [])

    scored = score_customer(customer_data, transactions, enquiries)
    product = recommend_product(scored)
    scored["recommended_product"] = product["name"] if product else None
    scored["product_details"] = product

    return scored
