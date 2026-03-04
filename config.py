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
SERPER_API_KEY = "819898aee815aa3c0cf7762a22b32200a13f736c"

# Anthropic Claude API
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY_HERE"

# Search Configuration
DEFAULT_QUERIES_COUNT = 10  # Each query returns up to 10 results
RESULTS_PER_QUERY = 10

# File Paths
CV_PATH = "CV.pdf"
PROFILE_OUTPUT_PATH = "profile_output.csv"
MESSAGE_OUTPUT_PATH = "message_output.csv"

# Query Generation Paths
QUERIES_FOLDER = "queries"
QUERY_PARAMS_PATH = "queries/query_params.txt"
RANKED_QUERIES_PATH = "queries/ranked_queries.csv"
CV_QUERIES_PATH = "queries/cv_queries.csv"

# Similarity Settings
TFIDF_MAX_FEATURES = 5000

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
