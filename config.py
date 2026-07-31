import os
from dotenv import load_dotenv

# Load env files
load_dotenv()

# MongoDB configuration settings
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "legal_assistant_db")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6KFaRauPNAu1t0skJ1cIcT72XBzkbFkbecnA78GTTj9yA").strip()

# SMTP configuration for emails
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# Default fallback schemes in case DB is empty
DEFAULT_SCHEMES = [
    {
        "id": "pm_kisan",
        "name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "category": "Agriculture",
        "description": "An initiative by the government of India that provides up to ₹6,000 per year in three equal installments to small and marginal farmers.",
        "eligibility": "All landholding farmers' families in the country are eligible. Land records must be in the farmer's name.",
        "benefits": "₹6,000 per year, paid as ₹2,000 every four months directly into the bank accounts of farmers.",
        "required_documents": ["Aadhaar Card", "Land holding papers/record", "Bank Account Details", "Mobile Number linked with Aadhaar"]
    },
    {
        "id": "pmsym",
        "name": "Pradhan Mantri Shram Yogi Maan-dhan (PM-SYM)",
        "category": "Social Welfare & Pension",
        "description": "A voluntary and contributory pension scheme for unorganized workers like street vendors, rickshaw pullers, and domestic workers.",
        "eligibility": "Should be an unorganised worker aged between 18 and 40 years. Monthly income should be ₹15,000 or less.",
        "benefits": "Assured monthly pension of ₹3,000 after attaining the age of 60 years.",
        "required_documents": ["Aadhaar Card", "Savings Bank Account Passbook", "Active Mobile Number"]
    },
    {
        "id": "pm_awas_yojana",
        "name": "Pradhan Mantri Awas Yojana (PMAY) - Urban & Gramin",
        "category": "Housing",
        "description": "Provides affordable housing for the urban and rural poor with a target of building energy-efficient houses.",
        "eligibility": "Families belonging to EWS (Economically Weaker Section) with annual income up to ₹3 Lakh, LIG (Low Income Group) up to ₹6 Lakh, or MIG (Middle Income Group) up to ₹12-18 Lakh. The beneficiary family should not own a pucca house in their name anywhere in India.",
        "benefits": "Interest subsidy on home loans ranging from 3% to 6.5% depending on income category, or direct financial assistance for house construction.",
        "required_documents": ["Aadhaar Card", "Income Certificate", "Address Proof", "Affidavit stating no ownership of other houses", "Bank Passbook"]
    },
    {
        "id": "pmsis",
        "name": "Post Matric Scholarship Scheme",
        "category": "Education",
        "description": "Financial assistance to students belonging to Scheduled Castes, Scheduled Tribes, and other backward classes to pursue higher education.",
        "eligibility": "Students enrolled in post-matriculation or post-secondary courses. Parent's annual income must not exceed ₹2.5 Lakh.",
        "benefits": "100% reimbursement of tuition fees and a monthly maintenance allowance.",
        "required_documents": ["Aadhaar Card", "Income Certificate", "Caste Certificate", "Mark sheets of qualifying examinations", "Fee Receipt", "Bank Passbook"]
    }
]
