"""
Query Generator - Creates and ranks LinkedIn X-ray search queries

Supports two flows:
1. Permutation ranking - Generate all permutations from params file, rank by CV similarity
2. Direct CV generation - Rule-based query extraction from CV content
"""

import csv
import re
from itertools import product
from pathlib import Path
from typing import Optional

import config
from cv_parser import parse_cv
from embedding_utils import calculate_query_similarities


def parse_query_params(filepath: str) -> dict[str, list[str]]:
    """Parse query_params.txt file format into dict of lists."""
    params = {}
    current_section = None

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1].lower()
                params[current_section] = []
            elif current_section:
                params[current_section].append(line)

    return params


def generate_permutations(params: dict[str, list[str]]) -> list[str]:
    """Generate all query permutations from params dict."""
    locations = params.get("locations", [])
    seniorities = params.get("seniority", [])
    roles = params.get("roles", [])

    queries = []
    for location, seniority, role in product(locations, seniorities, roles):
        query = f'site:linkedin.com/in "{location}" "{seniority}" "{role}"'
        queries.append(query)

    return queries


def rank_queries_by_cv(queries: list[str], cv_path: str) -> list[dict]:
    """Rank queries by TF-IDF similarity to CV text."""
    cv_data = parse_cv(cv_path)
    cv_text = cv_data.get("raw_text", "")

    print(f"Processing CV text ({len(cv_text)} chars)...")
    print(f"Calculating similarities for {len(queries)} queries...")

    similarities = calculate_query_similarities(queries, cv_text)

    ranked = []
    for query, score in zip(queries, similarities):
        ranked.append({
            "query": query,
            "similarity_score": round(float(score), 4),
        })

    ranked.sort(key=lambda x: x["similarity_score"], reverse=True)

    for i, item in enumerate(ranked, 1):
        item["rank"] = i

    return ranked


def save_ranked_queries_csv(ranked_queries: list[dict], output_path: str):
    """Save ranked queries to CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["rank", "query", "similarity_score"])
        writer.writeheader()
        writer.writerows(ranked_queries)

    print(f"Saved {len(ranked_queries)} ranked queries to {output_path}")


def generate_cv_specific_queries(cv_data: dict, count: int = 5) -> list[dict]:
    """Generate highly CV-specific queries from recent experience."""
    queries = []
    experience = cv_data.get("experience", [])
    keywords = cv_data.get("keywords", [])

    locations = [k for k in keywords if k.lower() in [l.lower() for l in config.LOCATIONS]]
    if not locations:
        locations = ["Indonesia"]

    if experience:
        recent = experience[0]
        company = recent.get("company", "")
        title = recent.get("title", "")

        if company and title:
            for loc in locations[:2]:
                queries.append({
                    "category": "highly_specific",
                    "query": f'site:linkedin.com/in "{company}" "{title}"',
                })

        if company:
            queries.append({
                "category": "highly_specific",
                "query": f'site:linkedin.com/in "{company}"',
            })

    industries = [k for k in keywords if k.lower() in [i.lower() for i in config.INDUSTRIES]]
    seniorities = [k for k in keywords if k.lower() in [s.lower() for s in config.SENIORITY_LEVELS]]

    if industries and experience:
        recent_title = experience[0].get("title", "") if experience else ""
        for industry in industries[:2]:
            for loc in locations[:2]:
                if recent_title:
                    queries.append({
                        "category": "highly_specific",
                        "query": f'site:linkedin.com/in "{industry}" "{recent_title}" {loc}',
                    })

    if seniorities and experience:
        recent_title = experience[0].get("title", "") if experience else ""
        for seniority in seniorities[:1]:
            for loc in locations[:2]:
                if recent_title:
                    queries.append({
                        "category": "highly_specific",
                        "query": f'site:linkedin.com/in "{seniority}" "{recent_title}" {loc}',
                    })

    seen = set()
    unique_queries = []
    for q in queries:
        if q["query"] not in seen:
            seen.add(q["query"])
            unique_queries.append(q)

    return unique_queries[:count]


def generate_cv_broad_queries(cv_data: dict, count: int = 5) -> list[dict]:
    """Generate broadly CV-similar queries from skills and keywords."""
    queries = []
    skills = cv_data.get("skills", [])
    keywords = cv_data.get("keywords", [])

    locations = [k for k in keywords if k.lower() in [l.lower() for l in config.LOCATIONS]]
    if not locations:
        locations = ["Indonesia"]

    industries = [k for k in keywords if k.lower() in [i.lower() for i in config.INDUSTRIES]]
    roles = [k for k in keywords if k.lower() in [r.lower() for r in config.ROLES]]

    for industry in industries[:2]:
        for role in roles[:2]:
            for loc in locations[:2]:
                queries.append({
                    "category": "broadly_similar",
                    "query": f'site:linkedin.com/in "{industry}" "{role}" {loc}',
                })

    skill_keywords = [s for s in skills if len(s) > 3][:5]
    for skill in skill_keywords:
        skill_clean = re.sub(r'[^\w\s]', '', skill)
        if skill_clean:
            for loc in locations[:1]:
                queries.append({
                    "category": "broadly_similar",
                    "query": f'site:linkedin.com/in "{skill_clean}" {loc}',
                })

    for role in roles[:3]:
        for loc in locations[:2]:
            queries.append({
                "category": "broadly_similar",
                "query": f'site:linkedin.com/in "{role}" {loc}',
            })

    seen = set()
    unique_queries = []
    for q in queries:
        if q["query"] not in seen:
            seen.add(q["query"])
            unique_queries.append(q)

    return unique_queries[:count]


def save_cv_queries_csv(queries: list[dict], output_path: str):
    """Save CV-generated queries to CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["category", "query"])
        writer.writeheader()
        writer.writerows(queries)

    print(f"Saved {len(queries)} queries to {output_path}")


# Legacy functions for backwards compatibility
def generate_queries(max_queries: int = 10) -> list[dict]:
    """Generate a balanced set of queries using default configuration."""
    queries = []

    for role in config.ROLES:
        for location in config.LOCATIONS[:2]:
            queries.append({
                "query": f'site:linkedin.com/in "{role}" "{location}"',
                "type": "professional",
                "metadata": {"role": role, "location": location},
            })

    for role in config.ROLES[:3]:
        for location in config.LOCATIONS[:2]:
            for seniority in config.SENIORITY_LEVELS[:2]:
                queries.append({
                    "query": f'site:linkedin.com/in "{role}" "{location}" {seniority}',
                    "type": "professional_seniority",
                    "metadata": {"role": role, "location": location, "seniority": seniority},
                })

    seen = set()
    unique_queries = []
    for q in queries:
        if q["query"] not in seen:
            seen.add(q["query"])
            unique_queries.append(q)

    return unique_queries[:max_queries]


def generate_queries_from_cv(cv_data: dict, max_queries: int = 10) -> list[dict]:
    """Generate queries based on CV content (legacy format)."""
    all_queries = []

    specific = generate_cv_specific_queries(cv_data, count=max_queries // 2)
    for q in specific:
        all_queries.append({
            "query": q["query"],
            "type": "cv_specific",
            "metadata": {},
        })

    broad = generate_cv_broad_queries(cv_data, count=max_queries // 2)
    for q in broad:
        all_queries.append({
            "query": q["query"],
            "type": "cv_broad",
            "metadata": {},
        })

    return all_queries[:max_queries]


if __name__ == "__main__":
    print("Query Generator Test")
    print("=" * 50)

    params_path = config.QUERY_PARAMS_PATH
    if Path(params_path).exists():
        print(f"\nParsing {params_path}...")
        params = parse_query_params(params_path)
        print(f"  Locations: {params.get('locations', [])}")
        print(f"  Seniorities: {params.get('seniority', [])}")
        print(f"  Roles: {params.get('roles', [])}")

        queries = generate_permutations(params)
        print(f"\nGenerated {len(queries)} permutations")
        for q in queries[:5]:
            print(f"  {q}")
    else:
        print(f"\nNo {params_path} found. Creating sample...")
