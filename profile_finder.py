"""
Profile Finder - Serper.dev API integration for LinkedIn profile discovery
"""

import csv
import re
from typing import Optional

import pandas as pd
import requests

import config


SERPER_API_URL = "https://google.serper.dev/search"


def load_queries_from_csv(filepath: str, top_n: Optional[int] = None) -> list[dict]:
    """Load queries from a CSV file (ranked_queries.csv or cv_queries.csv format)."""
    queries = []

    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            query_text = row.get("query", "")
            if not query_text:
                continue

            query_type = row.get("category", "csv_loaded")
            if "rank" in row:
                query_type = "ranked"

            queries.append({
                "query": query_text,
                "type": query_type,
                "metadata": row,
            })

    if top_n and top_n > 0:
        queries = queries[:top_n]

    return queries


def execute_search(query: str, num_results: int = 10) -> list[dict]:
    """Execute a single search query using Serper.dev API and return parsed results."""
    if config.SERPER_API_KEY == "YOUR_SERPER_API_KEY_HERE":
        raise ValueError(
            "Serper API key not configured. "
            "Please set SERPER_API_KEY in config.py. "
            "Sign up at https://serper.dev/ to get your free API key."
        )

    headers = {
        "X-API-KEY": config.SERPER_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "q": query,
        "num": min(num_results, 100),  # Serper allows up to 100
    }

    try:
        response = requests.post(SERPER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("organic", []):
            url = item.get("link", "")

            # Only process LinkedIn profile URLs
            if "linkedin.com/in/" not in url:
                continue

            title = item.get("title", "")
            snippet = item.get("snippet", "")

            profile_data = parse_linkedin_snippet(title, snippet)
            profile_data["linkedin_url"] = url
            profile_data["raw_title"] = title
            profile_data["raw_snippet"] = snippet

            # Extract attributes if available
            attributes = item.get("attributes", [])
            profile_data["attributes"] = "; ".join(attributes) if attributes else ""

            results.append(profile_data)

        return results

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise ValueError(
                "Invalid Serper API key. "
                "Please check your SERPER_API_KEY in config.py."
            )
        elif e.response.status_code == 403:
            raise ValueError(
                "Serper API access denied. "
                "Your API key may have exceeded its quota."
            )
        raise ValueError(f"Serper API error: {e}")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Network error: {e}")


def parse_linkedin_snippet(title: str, snippet: str) -> dict:
    """
    Parse LinkedIn search result to extract profile information.

    Returns dict with name, profile_title, job_title, company, location.
    """
    result = {
        "name": "",
        "profile_title": "",
        "job_title": "",
        "company": "",
        "location": "",
    }

    # Name is typically before the first dash or pipe in title
    # Format: "Name - Title | LinkedIn" or "Name | Title - Company | LinkedIn"
    title_clean = title.replace(" | LinkedIn", "").replace(" - LinkedIn", "")

    parts = re.split(r"\s*[-|]\s*", title_clean)
    if parts:
        result["name"] = parts[0].strip()
        if len(parts) > 1:
            result["profile_title"] = parts[1].strip()

    # Try to extract job title and company from profile_title
    # Common format: "Job Title at Company"
    if result["profile_title"]:
        at_match = re.match(r"(.+?)\s+at\s+(.+)", result["profile_title"], re.IGNORECASE)
        if at_match:
            result["job_title"] = at_match.group(1).strip()
            result["company"] = at_match.group(2).strip()
        else:
            result["job_title"] = result["profile_title"]

    # Try to find location in snippet
    location_patterns = [
        r"(?:Location|Based in|Located in)[:\s]+([^\.]+)",
        r"(Jakarta|Singapore|Indonesia|Malaysia|Bangkok|Manila|Vietnam|Philippines|APAC|Dubai)",
        r"([A-Z][a-z]+,\s*[A-Z][a-z]+)",  # City, Country format
    ]

    for pattern in location_patterns:
        match = re.search(pattern, snippet, re.IGNORECASE)
        if match:
            result["location"] = match.group(1).strip()
            break

    return result


def calculate_match_score(profile_text: str, cv_keywords: list[str]) -> float:
    """
    Calculate match score between profile and CV keywords.

    Score = (matched_keywords / total_cv_keywords) * 100

    Includes bonus points for:
    - Same industry keywords
    - Relevant seniority level
    - Location match
    """
    if not cv_keywords:
        return 0.0

    profile_lower = profile_text.lower()
    matched = sum(1 for kw in cv_keywords if kw.lower() in profile_lower)

    base_score = (matched / len(cv_keywords)) * 100

    # Bonus for seniority matches (max +10)
    seniority_bonus = 0
    for level in config.SENIORITY_LEVELS:
        if level.lower() in profile_lower:
            seniority_bonus = 10
            break

    # Bonus for industry matches (max +10)
    industry_bonus = 0
    for industry in config.INDUSTRIES:
        if industry.lower() in profile_lower:
            industry_bonus = 10
            break

    # Bonus for location matches (max +5)
    location_bonus = 0
    for location in config.LOCATIONS:
        if location.lower() in profile_lower:
            location_bonus = 5
            break

    total_score = min(100, base_score + seniority_bonus + industry_bonus + location_bonus)
    return round(total_score, 2)


def find_profiles(
    queries: list[dict],
    cv_keywords: Optional[list[str]] = None,
    output_path: Optional[str] = None,
    results_per_query: Optional[int] = None,
) -> pd.DataFrame:
    """
    Execute queries and find LinkedIn profiles.

    Args:
        queries: List of query dicts from query_generator
        cv_keywords: Keywords from CV for match scoring
        output_path: Path to save CSV (defaults to config.PROFILE_OUTPUT_PATH)
        results_per_query: Number of results per query (defaults to config.RESULTS_PER_QUERY)

    Returns:
        DataFrame with profile data
    """
    cv_keywords = cv_keywords or []
    output_path = output_path or config.PROFILE_OUTPUT_PATH
    results_per_query = results_per_query or config.RESULTS_PER_QUERY

    all_profiles = []
    seen_urls = set()

    print(f"Executing {len(queries)} queries...")

    for i, query_data in enumerate(queries, 1):
        query = query_data["query"]
        query_type = query_data.get("type", "unknown")

        print(f"  [{i}/{len(queries)}] {query_type}: {query[:60]}...")

        try:
            results = execute_search(query, num_results=results_per_query)

            for profile in results:
                url = profile["linkedin_url"]

                # Skip duplicates
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # Add metadata
                profile["query_source"] = query
                profile["query_type"] = query_type

                # Calculate match score
                profile_text = " ".join([
                    profile.get("name", ""),
                    profile.get("profile_title", ""),
                    profile.get("raw_snippet", ""),
                ])
                profile["match_score"] = calculate_match_score(profile_text, cv_keywords)

                # Email placeholder
                profile["email"] = ""

                all_profiles.append(profile)

            print(f"      Found {len(results)} profiles ({len(all_profiles)} total unique)")

        except ValueError as e:
            print(f"      Error: {e}")
            break
        except Exception as e:
            print(f"      Error executing query: {e}")
            continue

    if not all_profiles:
        print("\nNo profiles found.")
        return pd.DataFrame()

    # Create DataFrame and sort by match score
    df = pd.DataFrame(all_profiles)

    # Reorder columns
    columns = [
        "name",
        "profile_title",
        "job_title",
        "company",
        "location",
        "linkedin_url",
        "email",
        "match_score",
        "attributes",
        "query_source",
    ]
    # Only include columns that exist
    columns = [c for c in columns if c in df.columns]
    df = df[columns]

    # Sort by match score descending
    df = df.sort_values("match_score", ascending=False)

    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"\nSaved {len(df)} profiles to {output_path}")

    return df


if __name__ == "__main__":
    from query_generator import generate_queries

    # Test with a few queries
    queries = generate_queries(max_queries=2)
    print("Testing profile finder with 2 queries...")

    try:
        df = find_profiles(queries)
        if not df.empty:
            print("\nTop 5 profiles by match score:")
            print(df.head()[["name", "profile_title", "match_score"]])
    except ValueError as e:
        print(f"\nConfiguration error: {e}")
