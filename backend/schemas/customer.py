"""Pydantic v2 schemas for customer data."""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date, datetime


class LoanInfo(BaseModel):
    type: str
    emi: float
    outstanding: float


class CustomerBase(BaseModel):
    name: str
    age: int
    phone: str
    email: str
    city: str
    occupation: str
    monthly_income: float
    credit_score: int
    existing_loans: List[Dict[str, Any]] = []
    account_balance: float
    account_type: str
    risk_profile: str


class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_since: date
    last_interaction_date: Optional[date] = None
    relationship_manager_id: Optional[str] = None
    kyc_status: str


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    transaction_date: datetime
    amount: float
    transaction_type: str
    category: Optional[str] = None
    description: Optional[str] = None
    merchant: Optional[str] = None


class LoanEnquiryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    enquiry_date: datetime
    product_type: str
    amount_requested: Optional[float] = None
    status: str


class ScoredCustomer(CustomerResponse):
    """Customer enriched with scoring and product recommendation."""

    conversion_score: float = 0.0
    conversion_probability: float = 0.0
    score_breakdown: Dict[str, float] = {}
    score_reasoning: str = ""
    recommended_product: Optional[str] = None
    product_details: Optional[Dict[str, Any]] = None
    loan_enquiry: Optional[LoanEnquiryResponse] = None


class CustomerDetailResponse(CustomerResponse):
    """Full customer profile with related data."""

    transactions: List[TransactionResponse] = []
    loan_enquiries: List[LoanEnquiryResponse] = []
