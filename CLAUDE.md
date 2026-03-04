# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JobProfileFinder is a LinkedIn prospect finder and cold outreach message generator. It uses Serper.dev API for X-ray LinkedIn searches and Anthropic Claude API for generating personalized messages.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Query generation - Flow 1: Permutation ranking by CV similarity
python main.py query-rank --params queries/query_params.txt --cv CV.pdf
# Output: queries/ranked_queries.csv (default)

# Query generation - Flow 2: Direct CV extraction
python main.py query-cv --cv CV.pdf
python main.py query-cv --cv CV.pdf --specific 5 --broad 5

# Find LinkedIn profiles (runs search queries)
python main.py find
python main.py find --queries 5        # Limit to 5 queries
python main.py find --cv path/to/cv.pdf
python main.py find --query-file queries/ranked_queries.csv --top 10 --results 10
python main.py find --query-file queries/cv_queries.csv --results 10

# Generate personalized messages for found profiles
python main.py generate
python main.py generate --limit 10     # Only process top 10 profiles

# Run full pipeline (find + generate)
python main.py run
```

## Architecture

```
main.py                 # CLI entry point with subcommands: query-rank, query-cv, find, generate, run
    ├── cv_parser.py        # Extracts text/skills/keywords from CV.pdf using pdfplumber
    ├── query_generator.py  # Creates X-ray queries (permutation ranking or CV extraction)
    ├── embedding_utils.py  # Sentence embeddings for query ranking (sentence-transformers)
    ├── profile_finder.py   # Executes Serper.dev API searches, parses LinkedIn results
    └── message_generator.py # Calls Claude API to craft personalized outreach messages

config.py               # API keys, search parameters, file paths
queries/                # Input/output folder for query files
    ├── query_params.txt    # User-defined parameter lists (locations, seniority, roles)
    ├── ranked_queries.csv  # Output: queries ranked by CV similarity
    └── cv_queries.csv      # Output: queries extracted from CV content
```

**Data flow (two query generation flows):**

Flow 1 - Permutation Ranking:
1. User defines parameters in `queries/query_params.txt`
2. `query_generator` creates all permutations and ranks by CV embedding similarity
3. Output: `queries/ranked_queries.csv` with similarity scores

Flow 2 - Direct CV Extraction:
1. `cv_parser` extracts keywords/experience from CV
2. `query_generator` creates highly_specific and broadly_similar queries
3. Output: `queries/cv_queries.csv`

Profile Search:
1. `profile_finder` loads queries from CSV or generates them
2. Executes queries via Serper.dev, outputs `profile_output.csv`
3. `message_generator` reads profiles, calls Claude API, outputs `message_output.csv`

## Configuration

Edit `config.py` to set:
- `SERPER_API_KEY` - from https://serper.dev/ (free tier: 2,500 searches)
- `ANTHROPIC_API_KEY` - from https://console.anthropic.com/
- `ROLES`, `LOCATIONS`, `INDUSTRIES` - customize search targeting

## PRD Directory & Change Requests

Whenever a change request is made that differs from the initial requirements in `PRD/initial_prd.txt`, create a new `.txt` file in the `/PRD` directory:

- **Filename format:** `change_NNN_description.txt` (e.g., `change_001_serper_migration.txt`)
- **Required sections:**
  - Summary of the change
  - Reason for change (why it was needed)
  - Before state (what it was)
  - After state (what it became)
  - Files modified
  - Migration/testing steps if applicable
