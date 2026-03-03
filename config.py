"""
Configuration for ProspectFinder

API Keys Setup Instructions:
----------------------------

1. SERPER_API_KEY:
   - Go to https://serper.dev/
   - Sign up for a free account
   - Go to Dashboard > API Key
   - Copy your API key
   - Free tier: 2,500 searches (one-time credit)

2. ANTHROPIC_API_KEY:
   - Go to https://console.anthropic.com/
   - Create an account and go to API Keys
   - Generate a new API key
"""

# Serper.dev API (Google Search)
SERPER_API_KEY = "YOUR_SERPER_API_KEY_HERE"

# Anthropic Claude API
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY_HERE"

# Search Configuration
DEFAULT_QUERIES_COUNT = 10  # Each query returns up to 10 results
RESULTS_PER_QUERY = 10

# File Paths
CV_PATH = "CV.pdf"
PROFILE_OUTPUT_PATH = "profile_output.csv"
MESSAGE_OUTPUT_PATH = "message_output.csv"

# Query Parameters
ROLES = [
    "product manager",
    "data analyst",
    "business analyst",
    "project manager",
    "BI analyst",
]

LOCATIONS = [
    "Indonesia",
    "Jakarta",
    "Singapore",
    "Dubai",
    "APAC",
]

SENIORITY_LEVELS = [
    "senior",
    "lead",
    "head",
    "manager",
    "director",
]

INDUSTRIES = [
    "technology",
    "e-commerce",
    "fintech",
    "logistics",
    "FMCG",
]
