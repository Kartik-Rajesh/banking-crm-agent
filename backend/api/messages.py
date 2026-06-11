"""REST endpoints for WhatsApp message generation."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.tools.db_tools import get_customer_by_id
from backend.tools.scoring_tools import score_customer, recommend_product, LOAN_PRODUCTS
from backend.tools.message_tools import generate_whatsapp_messages

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/messages", tags=["messages"])


class GenerateRequest(BaseModel):
    customer_id: int
    product: Optional[str] = None
    tone: Optional[str] = None  # specific tone override


@router.post("/generate")
async def generate_messages_endpoint(request: GenerateRequest):
    """Generate 3 WhatsApp message variants for a customer."""
    customer_data = get_customer_by_id(request.customer_id)
    if not customer_data:
        raise HTTPException(status_code=404, detail=f"Customer {request.customer_id} not found")

    transactions = customer_data.get("transactions", [])
    enquiries = customer_data.get("loan_enquiries", [])

    scored = score_customer(customer_data, transactions, enquiries)

    # Determine product
    if request.product:
        product = next(
            (p for p in LOAN_PRODUCTS if p["name"].lower() == request.product.lower()),
            None,
        )
    else:
        product = recommend_product(scored)

    if not product:
        product = LOAN_PRODUCTS[1]  # Default to Standard Salaried

    try:
        variants = generate_whatsapp_messages(scored, product)
    except Exception as e:
        logger.error(f"Message generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Message generation failed: {str(e)}")

    return {
        "success": True,
        "customer_id": request.customer_id,
        "customer_name": customer_data["name"],
        "product": product["name"],
        "variants": variants,
    }
