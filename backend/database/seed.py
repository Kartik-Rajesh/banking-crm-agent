"""Seed 50 realistic Indian banking customers with transaction history."""

import random
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from backend.database.models import Customer, Transaction, LoanEnquiry
from backend.database.connection import engine, Base


CUSTOMERS_DATA = [
    # Mumbai - High earners
    {
        "name": "Rahul Kumar", "age": 34, "phone": "9821054321", "email": "rahul.kumar@infosys.com",
        "city": "Mumbai", "occupation": "SALARIED", "monthly_income": 125000,
        "credit_score": 780, "account_balance": 285000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [{"type": "HOME_LOAN", "emi": 32000, "outstanding": 2800000}],
        "has_recent_enquiry": True, "enquiry_days_ago": 12,
    },
    {
        "name": "Priya Sharma", "age": 29, "phone": "9920184532", "email": "priya.sharma@tcs.com",
        "city": "Mumbai", "occupation": "SALARIED", "monthly_income": 95000,
        "credit_score": 755, "account_balance": 180000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Amit Desai", "age": 42, "phone": "9867432198", "email": "amit.desai@businesscorp.com",
        "city": "Mumbai", "occupation": "SELF_EMPLOYED", "monthly_income": 320000,
        "credit_score": 810, "account_balance": 750000, "account_type": "CURRENT",
        "risk_profile": "LOW", "existing_loans": [{"type": "HOME_LOAN", "emi": 75000, "outstanding": 8500000}],
        "has_recent_enquiry": True, "enquiry_days_ago": 25,
    },
    {
        "name": "Sunita Mehta", "age": 38, "phone": "9819876543", "email": "sunita.mehta@wipro.com",
        "city": "Mumbai", "occupation": "SALARIED", "monthly_income": 88000,
        "credit_score": 720, "account_balance": 145000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [{"type": "CAR_LOAN", "emi": 12000, "outstanding": 380000}],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Vikram Nair", "age": 45, "phone": "9820543210", "email": "vikram.nair@hdfcbank.com",
        "city": "Mumbai", "occupation": "SALARIED", "monthly_income": 180000,
        "credit_score": 795, "account_balance": 420000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [{"type": "HOME_LOAN", "emi": 45000, "outstanding": 4200000}],
        "has_recent_enquiry": True, "enquiry_days_ago": 8,
    },
    # Delhi - Mix of profiles
    {
        "name": "Ananya Gupta", "age": 27, "phone": "9811234567", "email": "ananya.gupta@amazon.in",
        "city": "Delhi", "occupation": "SALARIED", "monthly_income": 78000,
        "credit_score": 710, "account_balance": 95000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": True, "enquiry_days_ago": 20,
    },
    {
        "name": "Rajesh Agarwal", "age": 51, "phone": "9810765432", "email": "rajesh.agarwal@delhitraders.com",
        "city": "Delhi", "occupation": "SELF_EMPLOYED", "monthly_income": 250000,
        "credit_score": 740, "account_balance": 580000, "account_type": "CURRENT",
        "risk_profile": "MEDIUM", "existing_loans": [{"type": "HOME_LOAN", "emi": 55000, "outstanding": 6200000}],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Neha Joshi", "age": 32, "phone": "9899543210", "email": "neha.joshi@flipkart.com",
        "city": "Delhi", "occupation": "SALARIED", "monthly_income": 105000,
        "credit_score": 765, "account_balance": 220000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": True, "enquiry_days_ago": 5,
    },
    {
        "name": "Deepak Saxena", "age": 39, "phone": "9813456789", "email": "deepak.saxena@gmail.com",
        "city": "Delhi", "occupation": "SALARIED", "monthly_income": 55000,
        "credit_score": 680, "account_balance": 65000, "account_type": "SAVINGS",
        "risk_profile": "MEDIUM", "existing_loans": [{"type": "CAR_LOAN", "emi": 9500, "outstanding": 220000}],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Kavita Singh", "age": 35, "phone": "9818765432", "email": "kavita.singh@accenture.com",
        "city": "Delhi", "occupation": "SALARIED", "monthly_income": 92000,
        "credit_score": 735, "account_balance": 175000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    # Bangalore - Tech sector
    {
        "name": "Arjun Reddy", "age": 30, "phone": "9845123456", "email": "arjun.reddy@google.com",
        "city": "Bangalore", "occupation": "SALARIED", "monthly_income": 195000,
        "credit_score": 800, "account_balance": 520000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": True, "enquiry_days_ago": 3,
    },
    {
        "name": "Divya Krishnamurthy", "age": 28, "phone": "9844234567", "email": "divya.k@microsoft.com",
        "city": "Bangalore", "occupation": "SALARIED", "monthly_income": 145000,
        "credit_score": 775, "account_balance": 310000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Suresh Rao", "age": 44, "phone": "9880345678", "email": "suresh.rao@startup.io",
        "city": "Bangalore", "occupation": "SELF_EMPLOYED", "monthly_income": 180000,
        "credit_score": 720, "account_balance": 390000, "account_type": "CURRENT",
        "risk_profile": "LOW", "existing_loans": [{"type": "HOME_LOAN", "emi": 42000, "outstanding": 3800000}],
        "has_recent_enquiry": True, "enquiry_days_ago": 45,
    },
    {
        "name": "Meera Iyer", "age": 31, "phone": "9845678901", "email": "meera.iyer@infosys.com",
        "city": "Bangalore", "occupation": "SALARIED", "monthly_income": 82000,
        "credit_score": 695, "account_balance": 115000, "account_type": "SALARY",
        "risk_profile": "MEDIUM", "existing_loans": [{"type": "EDUCATION_LOAN", "emi": 8000, "outstanding": 180000}],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Karthik Subramanian", "age": 36, "phone": "9880912345", "email": "karthik.s@oracle.com",
        "city": "Bangalore", "occupation": "SALARIED", "monthly_income": 165000,
        "credit_score": 790, "account_balance": 450000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [{"type": "HOME_LOAN", "emi": 38000, "outstanding": 3400000}],
        "has_recent_enquiry": True, "enquiry_days_ago": 15,
    },
    # Pune - IT + Manufacturing mix
    {
        "name": "Pooja Patil", "age": 33, "phone": "9823456789", "email": "pooja.patil@persistent.com",
        "city": "Pune", "occupation": "SALARIED", "monthly_income": 75000,
        "credit_score": 725, "account_balance": 132000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": True, "enquiry_days_ago": 18,
    },
    {
        "name": "Sanjay Kulkarni", "age": 47, "phone": "9822345678", "email": "sanjay.k@tatamotors.com",
        "city": "Pune", "occupation": "SALARIED", "monthly_income": 130000,
        "credit_score": 755, "account_balance": 295000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [{"type": "HOME_LOAN", "emi": 28000, "outstanding": 2400000}],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Rashmi Bhosale", "age": 26, "phone": "9823901234", "email": "rashmi.bhosale@wipro.com",
        "city": "Pune", "occupation": "SALARIED", "monthly_income": 52000,
        "credit_score": 660, "account_balance": 48000, "account_type": "SALARY",
        "risk_profile": "MEDIUM", "existing_loans": [],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Mahesh Jain", "age": 53, "phone": "9821012345", "email": "mahesh.jain@jewelers.com",
        "city": "Pune", "occupation": "SELF_EMPLOYED", "monthly_income": 420000,
        "credit_score": 785, "account_balance": 1200000, "account_type": "CURRENT",
        "risk_profile": "LOW", "existing_loans": [{"type": "HOME_LOAN", "emi": 85000, "outstanding": 9500000}, {"type": "HOME_LOAN", "emi": 45000, "outstanding": 5200000}],
        "has_recent_enquiry": True, "enquiry_days_ago": 7,
    },
    {
        "name": "Sneha Deshpande", "age": 37, "phone": "9822678901", "email": "sneha.d@cognizant.com",
        "city": "Pune", "occupation": "SALARIED", "monthly_income": 98000,
        "credit_score": 748, "account_balance": 198000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": True, "enquiry_days_ago": 22,
    },
    # Hyderabad - Pharma + IT
    {
        "name": "Venkat Rao", "age": 41, "phone": "9989012345", "email": "venkat.rao@drreddy.com",
        "city": "Hyderabad", "occupation": "SALARIED", "monthly_income": 110000,
        "credit_score": 760, "account_balance": 245000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [{"type": "HOME_LOAN", "emi": 25000, "outstanding": 2200000}],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Lakshmi Prasad", "age": 36, "phone": "9900123456", "email": "lakshmi.p@wipro.com",
        "city": "Hyderabad", "occupation": "SALARIED", "monthly_income": 88000,
        "credit_score": 718, "account_balance": 158000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": True, "enquiry_days_ago": 14,
    },
    {
        "name": "Ramesh Choudhary", "age": 48, "phone": "9987654321", "email": "ramesh.c@pharmacy.com",
        "city": "Hyderabad", "occupation": "SELF_EMPLOYED", "monthly_income": 175000,
        "credit_score": 698, "account_balance": 320000, "account_type": "CURRENT",
        "risk_profile": "MEDIUM", "existing_loans": [{"type": "HOME_LOAN", "emi": 38000, "outstanding": 4100000}],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Swathi Reddy", "age": 29, "phone": "9912345678", "email": "swathi.reddy@amazon.in",
        "city": "Hyderabad", "occupation": "SALARIED", "monthly_income": 92000,
        "credit_score": 740, "account_balance": 185000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": True, "enquiry_days_ago": 28,
    },
    {
        "name": "Naresh Babu", "age": 44, "phone": "9985432109", "email": "naresh.babu@tech.com",
        "city": "Hyderabad", "occupation": "SALARIED", "monthly_income": 140000,
        "credit_score": 772, "account_balance": 335000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [{"type": "HOME_LOAN", "emi": 32000, "outstanding": 2800000}],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    # Additional diverse profiles
    {
        "name": "Chirag Shah", "age": 31, "phone": "9876543210", "email": "chirag.shah@finance.com",
        "city": "Mumbai", "occupation": "SALARIED", "monthly_income": 68000,
        "credit_score": 690, "account_balance": 82000, "account_type": "SALARY",
        "risk_profile": "MEDIUM", "existing_loans": [],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Pallavi Verma", "age": 40, "phone": "9871234567", "email": "pallavi.v@hospital.org",
        "city": "Delhi", "occupation": "SALARIED", "monthly_income": 115000,
        "credit_score": 758, "account_balance": 260000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": True, "enquiry_days_ago": 10,
    },
    {
        "name": "Manish Tiwari", "age": 35, "phone": "9856789012", "email": "manish.t@mfg.com",
        "city": "Pune", "occupation": "SALARIED", "monthly_income": 72000,
        "credit_score": 712, "account_balance": 98000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [{"type": "CAR_LOAN", "emi": 10500, "outstanding": 290000}],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Anjali Patel", "age": 43, "phone": "9898765432", "email": "anjali.patel@textiles.com",
        "city": "Mumbai", "occupation": "SELF_EMPLOYED", "monthly_income": 285000,
        "credit_score": 775, "account_balance": 620000, "account_type": "CURRENT",
        "risk_profile": "LOW", "existing_loans": [{"type": "HOME_LOAN", "emi": 62000, "outstanding": 7200000}],
        "has_recent_enquiry": True, "enquiry_days_ago": 6,
    },
    {
        "name": "Ravi Shankar", "age": 50, "phone": "9844567890", "email": "ravi.shankar@retail.com",
        "city": "Bangalore", "occupation": "SELF_EMPLOYED", "monthly_income": 380000,
        "credit_score": 820, "account_balance": 980000, "account_type": "CURRENT",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": True, "enquiry_days_ago": 2,
    },
    {
        "name": "Smita Chavan", "age": 28, "phone": "9876012345", "email": "smita.chavan@it.com",
        "city": "Pune", "occupation": "SALARIED", "monthly_income": 48000,
        "credit_score": 640, "account_balance": 35000, "account_type": "SALARY",
        "risk_profile": "HIGH", "existing_loans": [{"type": "EDUCATION_LOAN", "emi": 7000, "outstanding": 155000}],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Ganesh Murthy", "age": 46, "phone": "9845901234", "email": "ganesh.m@consulting.in",
        "city": "Bangalore", "occupation": "SELF_EMPLOYED", "monthly_income": 220000,
        "credit_score": 745, "account_balance": 495000, "account_type": "CURRENT",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Nisha Agarwal", "age": 33, "phone": "9891234567", "email": "nisha.a@school.edu",
        "city": "Delhi", "occupation": "SALARIED", "monthly_income": 42000,
        "credit_score": 670, "account_balance": 52000, "account_type": "SAVINGS",
        "risk_profile": "MEDIUM", "existing_loans": [],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Vijay Malhotra", "age": 55, "phone": "9810023456", "email": "vijay.m@exports.com",
        "city": "Delhi", "occupation": "SELF_EMPLOYED", "monthly_income": 500000,
        "credit_score": 830, "account_balance": 1500000, "account_type": "CURRENT",
        "risk_profile": "LOW", "existing_loans": [{"type": "HOME_LOAN", "emi": 95000, "outstanding": 10500000}],
        "has_recent_enquiry": True, "enquiry_days_ago": 19,
    },
    {
        "name": "Shweta Nambiar", "age": 30, "phone": "9846789012", "email": "shweta.n@flipkart.com",
        "city": "Bangalore", "occupation": "SALARIED", "monthly_income": 120000,
        "credit_score": 768, "account_balance": 275000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": True, "enquiry_days_ago": 11,
    },
    {
        "name": "Mohan Das", "age": 38, "phone": "9893456789", "email": "mohan.das@bank.com",
        "city": "Hyderabad", "occupation": "SALARIED", "monthly_income": 78000,
        "credit_score": 702, "account_balance": 125000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Preeti Kapoor", "age": 27, "phone": "9820987654", "email": "preeti.k@startup.com",
        "city": "Mumbai", "occupation": "SALARIED", "monthly_income": 85000,
        "credit_score": 728, "account_balance": 155000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": True, "enquiry_days_ago": 16,
    },
    {
        "name": "Ashok Pillai", "age": 49, "phone": "9844123456", "email": "ashok.pillai@mnc.com",
        "city": "Bangalore", "occupation": "SALARIED", "monthly_income": 210000,
        "credit_score": 805, "account_balance": 580000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [{"type": "HOME_LOAN", "emi": 48000, "outstanding": 4500000}],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Rekha Naidu", "age": 37, "phone": "9985678901", "email": "rekha.n@pharma.com",
        "city": "Hyderabad", "occupation": "SALARIED", "monthly_income": 95000,
        "credit_score": 742, "account_balance": 192000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": True, "enquiry_days_ago": 27,
    },
    {
        "name": "Sunil Bhat", "age": 45, "phone": "9820234567", "email": "sunil.bhat@finance.in",
        "city": "Mumbai", "occupation": "SALARIED", "monthly_income": 155000,
        "credit_score": 782, "account_balance": 365000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [{"type": "HOME_LOAN", "emi": 36000, "outstanding": 3200000}],
        "has_recent_enquiry": True, "enquiry_days_ago": 4,
    },
    {
        "name": "Geeta Mishra", "age": 32, "phone": "9871098765", "email": "geeta.m@media.com",
        "city": "Delhi", "occupation": "SALARIED", "monthly_income": 62000,
        "credit_score": 688, "account_balance": 78000, "account_type": "SALARY",
        "risk_profile": "MEDIUM", "existing_loans": [],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Prakash Hegde", "age": 41, "phone": "9880456789", "email": "prakash.h@engg.com",
        "city": "Bangalore", "occupation": "SALARIED", "monthly_income": 108000,
        "credit_score": 758, "account_balance": 238000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Usha Kothari", "age": 52, "phone": "9822567890", "email": "usha.k@retailchain.com",
        "city": "Pune", "occupation": "SELF_EMPLOYED", "monthly_income": 195000,
        "credit_score": 760, "account_balance": 445000, "account_type": "CURRENT",
        "risk_profile": "LOW", "existing_loans": [{"type": "HOME_LOAN", "emi": 42000, "outstanding": 3900000}],
        "has_recent_enquiry": True, "enquiry_days_ago": 23,
    },
    {
        "name": "Abhishek Tomar", "age": 26, "phone": "9811567890", "email": "abhishek.t@it.com",
        "city": "Delhi", "occupation": "SALARIED", "monthly_income": 38000,
        "credit_score": 620, "account_balance": 25000, "account_type": "SALARY",
        "risk_profile": "HIGH", "existing_loans": [],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Hema Krishnan", "age": 34, "phone": "9988234567", "email": "hema.k@ibm.com",
        "city": "Hyderabad", "occupation": "SALARIED", "monthly_income": 98000,
        "credit_score": 750, "account_balance": 212000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": True, "enquiry_days_ago": 9,
    },
    {
        "name": "Dinesh Sabnis", "age": 43, "phone": "9823789012", "email": "dinesh.s@autoparts.com",
        "city": "Pune", "occupation": "SELF_EMPLOYED", "monthly_income": 145000,
        "credit_score": 718, "account_balance": 315000, "account_type": "CURRENT",
        "risk_profile": "MEDIUM", "existing_loans": [{"type": "HOME_LOAN", "emi": 30000, "outstanding": 2700000}],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Sangita Roy", "age": 39, "phone": "9830123456", "email": "sangita.r@ngo.org",
        "city": "Mumbai", "occupation": "SALARIED", "monthly_income": 55000,
        "credit_score": 672, "account_balance": 68000, "account_type": "SAVINGS",
        "risk_profile": "MEDIUM", "existing_loans": [],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Tarun Walia", "age": 36, "phone": "9814567890", "email": "tarun.w@airline.com",
        "city": "Delhi", "occupation": "SALARIED", "monthly_income": 135000,
        "credit_score": 770, "account_balance": 305000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": True, "enquiry_days_ago": 13,
    },
    {
        "name": "Indira Rangan", "age": 44, "phone": "9847890123", "email": "indira.r@telecom.com",
        "city": "Bangalore", "occupation": "SALARIED", "monthly_income": 168000,
        "credit_score": 792, "account_balance": 410000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [{"type": "HOME_LOAN", "emi": 40000, "outstanding": 3600000}],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Kapil Sharma", "age": 29, "phone": "9870234567", "email": "kapil.s@startup.in",
        "city": "Delhi", "occupation": "SALARIED", "monthly_income": 72000,
        "credit_score": 715, "account_balance": 102000, "account_type": "SALARY",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": True, "enquiry_days_ago": 21,
    },
    {
        "name": "Anita Bose", "age": 48, "phone": "9831234567", "email": "anita.b@education.com",
        "city": "Mumbai", "occupation": "SALARIED", "monthly_income": 75000,
        "credit_score": 698, "account_balance": 118000, "account_type": "SAVINGS",
        "risk_profile": "MEDIUM", "existing_loans": [{"type": "HOME_LOAN", "emi": 18000, "outstanding": 1500000}],
        "has_recent_enquiry": False, "enquiry_days_ago": None,
    },
    {
        "name": "Harish Shetty", "age": 57, "phone": "9819012345", "email": "harish.s@properties.com",
        "city": "Mumbai", "occupation": "SELF_EMPLOYED", "monthly_income": 450000,
        "credit_score": 845, "account_balance": 2100000, "account_type": "CURRENT",
        "risk_profile": "LOW", "existing_loans": [],
        "has_recent_enquiry": True, "enquiry_days_ago": 1,
    },
]


def generate_transactions(customer: Customer, db: Session) -> None:
    """Generate 10-30 realistic transactions for a customer over 6 months."""
    today = datetime.now()
    salary_day = random.randint(1, 5)
    num_txns = random.randint(12, 28)

    # Always add 3 salary credits for salaried customers
    if customer.occupation == "SALARIED":
        for months_ago in range(3, 0, -1):
            salary_date = today - timedelta(days=months_ago * 30 - salary_day)
            txn = Transaction(
                customer_id=customer.id,
                transaction_date=salary_date,
                amount=customer.monthly_income,
                transaction_type="SALARY",
                category="INCOME",
                description=f"SALARY CREDIT - {salary_date.strftime('%b %Y')}",
                merchant="Employer",
            )
            db.add(txn)

    # Add EMI transactions for existing loans
    for loan in (customer.existing_loans or []):
        for months_ago in range(6, 0, -1):
            emi_date = today - timedelta(days=months_ago * 30 - 7)
            txn = Transaction(
                customer_id=customer.id,
                transaction_date=emi_date,
                amount=loan["emi"],
                transaction_type="EMI",
                category="LOAN_PAYMENT",
                description=f"{loan['type']} EMI",
                merchant="Bank Auto-Debit",
            )
            db.add(txn)

    # Regular spending transactions
    categories = [
        ("Groceries", ["BigBazaar", "Reliance Fresh", "Zepto"], 2000, 8000),
        ("Utilities", ["MSEB", "Bescom", "BSES"], 800, 3000),
        ("Dining", ["Zomato", "Swiggy", "Restaurant"], 500, 4000),
        ("Shopping", ["Amazon", "Flipkart", "Mall"], 1000, 15000),
        ("Transport", ["Ola", "Uber", "Metro"], 300, 2500),
        ("Medical", ["Apollo Pharmacy", "Hospital", "Clinic"], 500, 20000),
        ("Entertainment", ["BookMyShow", "Netflix", "PVR"], 300, 2000),
    ]

    for _ in range(num_txns):
        cat, merchants, min_amt, max_amt = random.choice(categories)
        days_ago = random.randint(1, 180)
        txn_date = today - timedelta(days=days_ago)

        txn = Transaction(
            customer_id=customer.id,
            transaction_date=txn_date,
            amount=random.uniform(min_amt, max_amt),
            transaction_type="DEBIT",
            category=cat,
            description=f"{cat} purchase",
            merchant=random.choice(merchants),
        )
        db.add(txn)

    # Some customers have large recent debits (renovation / medical — suggests loan need)
    if random.random() > 0.7:
        large_debit_date = today - timedelta(days=random.randint(15, 45))
        txn = Transaction(
            customer_id=customer.id,
            transaction_date=large_debit_date,
            amount=random.uniform(80000, 350000),
            transaction_type="DEBIT",
            category=random.choice(["Home Renovation", "Medical", "Wedding", "Education"]),
            description="Large cash outflow",
            merchant=random.choice(["Contractor Payment", "Hospital", "Caterer", "College"]),
        )
        db.add(txn)


def seed_database(db: Session) -> None:
    """Seed the database with all customers, transactions, and loan enquiries."""
    print("Seeding database with 50 realistic customers...")

    today = datetime.now()

    for i, data in enumerate(CUSTOMERS_DATA):
        # Randomize customer_since between 1-10 years ago
        years_ago = random.randint(1, 10)
        customer_since = date.today() - timedelta(days=years_ago * 365)
        last_interaction = date.today() - timedelta(days=random.randint(5, 90))

        customer = Customer(
            name=data["name"],
            age=data["age"],
            phone=data["phone"],
            email=data["email"],
            city=data["city"],
            occupation=data["occupation"],
            monthly_income=data["monthly_income"],
            credit_score=data["credit_score"],
            existing_loans=data["existing_loans"],
            account_balance=data["account_balance"],
            account_type=data["account_type"],
            customer_since=customer_since,
            last_interaction_date=last_interaction,
            relationship_manager_id="RM001",
            kyc_status="COMPLETE",
            risk_profile=data["risk_profile"],
        )
        db.add(customer)
        db.flush()  # Get the ID

        generate_transactions(customer, db)

        # Add loan enquiry if specified
        if data.get("has_recent_enquiry") and data.get("enquiry_days_ago"):
            enquiry_date = today - timedelta(days=data["enquiry_days_ago"])
            enquiry = LoanEnquiry(
                customer_id=customer.id,
                enquiry_date=enquiry_date,
                product_type="PERSONAL_LOAN",
                amount_requested=random.choice([200000, 300000, 500000, 750000, 1000000]),
                status="PENDING",
            )
            db.add(enquiry)

    db.commit()
    print(f"Seeded {len(CUSTOMERS_DATA)} customers with transactions and loan enquiries.")


def init_db() -> None:
    """Initialize database tables and seed data."""
    from backend.database.connection import SessionLocal

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Only seed if empty
        from backend.database.models import Customer
        if db.query(Customer).count() == 0:
            seed_database(db)
        else:
            print("Database already seeded, skipping.")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
