"""SQLAlchemy ORM models for the Banking CRM database."""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from backend.database.connection import Base


class RiskProfile(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TransactionType(str, enum.Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    EMI = "EMI"
    SALARY = "SALARY"


class LoanEnquiryStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DROPPED = "DROPPED"


class Customer(Base):
    """Core customer entity with banking profile."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    age = Column(Integer, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    city = Column(String, nullable=False, index=True)
    occupation = Column(String, nullable=False)  # SALARIED / SELF_EMPLOYED
    monthly_income = Column(Float, nullable=False)
    credit_score = Column(Integer, nullable=False)
    existing_loans = Column(JSON, default=list)  # List of {type, emi, outstanding}
    account_balance = Column(Float, nullable=False)
    account_type = Column(String, nullable=False)  # SAVINGS / CURRENT / SALARY
    customer_since = Column(Date, nullable=False)
    last_interaction_date = Column(Date, nullable=True)
    relationship_manager_id = Column(String, nullable=True)
    kyc_status = Column(String, default="COMPLETE")
    risk_profile = Column(String, default="MEDIUM")

    transactions = relationship("Transaction", back_populates="customer", cascade="all, delete-orphan")
    loan_enquiries = relationship("LoanEnquiry", back_populates="customer", cascade="all, delete-orphan")


class Transaction(Base):
    """Customer transaction history."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    transaction_date = Column(DateTime, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)
    category = Column(String, nullable=True)
    description = Column(String, nullable=True)
    merchant = Column(String, nullable=True)

    customer = relationship("Customer", back_populates="transactions")


class LoanEnquiry(Base):
    """Loan enquiry records — warm lead signals."""

    __tablename__ = "loan_enquiries"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    enquiry_date = Column(DateTime, nullable=False, index=True)
    product_type = Column(String, nullable=False)
    amount_requested = Column(Float, nullable=True)
    status = Column(String, default="PENDING")

    customer = relationship("Customer", back_populates="loan_enquiries")
