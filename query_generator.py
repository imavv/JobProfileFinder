"""
Query Generator - Creates Google X-ray search queries for LinkedIn profiles
"""

import random
from typing import Optional

import config


# Query templates for different search strategies
QUERY_TEMPLATES = {
    "professional": 'site:linkedin.com/in "{role}" "{location}"',
    "professional_seniority": 'site:linkedin.com/in "{role}" "{location}" {seniority}',
    "recruiter": 'site:linkedin.com/in recruiter "{industry}" "{location}"',
    "hiring": 'site:linkedin.com/in "hiring manager" OR "talent acquisition" "{location}"',
    "industry_role": 'site:linkedin.com/in "{role}" "{industry}"',
}


def generate_professional_queries(
    roles: Optional[list[str]] = None,
    locations: Optional[list[str]] = None,
    seniority_levels: Optional[list[str]] = None,
    max_queries: int = 10,
) -> list[dict]:
    """
    Generate professional role-based queries.

    Returns list of dicts with 'query' and 'metadata' keys.
    """
    roles = roles or config.ROLES
    locations = locations or config.LOCATIONS
    seniority_levels = seniority_levels or config.SENIORITY_LEVELS

    queries = []

    # Generate role + location combinations
    for role in roles:
        for location in locations:
            query = QUERY_TEMPLATES["professional"].format(
                role=role,
                location=location,
            )
            queries.append({
                "query": query,
                "type": "professional",
                "metadata": {
                    "role": role,
                    "location": location,
                },
            })

    # Add some with seniority
    for role in roles[:3]:  # Top 3 roles
        for location in locations[:2]:  # Top 2 locations
            for seniority in seniority_levels[:2]:  # Top 2 seniority levels
                query = QUERY_TEMPLATES["professional_seniority"].format(
                    role=role,
                    location=location,
                    seniority=seniority,
                )
                queries.append({
                    "query": query,
                    "type": "professional_seniority",
                    "metadata": {
                        "role": role,
                        "location": location,
                        "seniority": seniority,
                    },
                })

    # Shuffle and limit
    random.shuffle(queries)
    return queries[:max_queries]


def generate_recruiter_queries(
    industries: Optional[list[str]] = None,
    locations: Optional[list[str]] = None,
    max_queries: int = 5,
) -> list[dict]:
    """Generate queries targeting recruiters and hiring managers."""
    industries = industries or config.INDUSTRIES
    locations = locations or config.LOCATIONS

    queries = []

    # Recruiter queries
    for industry in industries:
        for location in locations[:2]:  # Top 2 locations
            query = QUERY_TEMPLATES["recruiter"].format(
                industry=industry,
                location=location,
            )
            queries.append({
                "query": query,
                "type": "recruiter",
                "metadata": {
                    "industry": industry,
                    "location": location,
                },
            })

    # Hiring manager queries
    for location in locations:
        query = QUERY_TEMPLATES["hiring"].format(location=location)
        queries.append({
            "query": query,
            "type": "hiring",
            "metadata": {
                "location": location,
            },
        })

    random.shuffle(queries)
    return queries[:max_queries]


def generate_industry_queries(
    roles: Optional[list[str]] = None,
    industries: Optional[list[str]] = None,
    max_queries: int = 5,
) -> list[dict]:
    """Generate queries combining roles with industries."""
    roles = roles or config.ROLES
    industries = industries or config.INDUSTRIES

    queries = []

    for role in roles:
        for industry in industries:
            query = QUERY_TEMPLATES["industry_role"].format(
                role=role,
                industry=industry,
            )
            queries.append({
                "query": query,
                "type": "industry_role",
                "metadata": {
                    "role": role,
                    "industry": industry,
                },
            })

    random.shuffle(queries)
    return queries[:max_queries]


def generate_queries_from_cv(cv_data: dict, max_queries: int = 10) -> list[dict]:
    """
    Generate optimized queries based on CV content.

    Uses CV keywords to prioritize relevant roles, industries, and locations.
    """
    keywords = cv_data.get("keywords", [])
    keywords_lower = [k.lower() for k in keywords]

    # Prioritize roles found in CV
    prioritized_roles = [r for r in config.ROLES if r.lower() in keywords_lower]
    roles = prioritized_roles + [r for r in config.ROLES if r not in prioritized_roles]

    # Prioritize locations found in CV
    prioritized_locations = [l for l in config.LOCATIONS if l.lower() in keywords_lower]
    locations = prioritized_locations + [l for l in config.LOCATIONS if l not in prioritized_locations]

    # Prioritize industries found in CV
    prioritized_industries = [i for i in config.INDUSTRIES if i.lower() in keywords_lower]
    industries = prioritized_industries + [i for i in config.INDUSTRIES if i not in prioritized_industries]

    # Generate mixed queries
    queries = []

    # 60% professional queries
    professional_count = int(max_queries * 0.6)
    queries.extend(generate_professional_queries(
        roles=roles,
        locations=locations,
        max_queries=professional_count,
    ))

    # 20% recruiter queries
    recruiter_count = int(max_queries * 0.2)
    queries.extend(generate_recruiter_queries(
        industries=industries,
        locations=locations,
        max_queries=recruiter_count,
    ))

    # 20% industry queries
    industry_count = max_queries - len(queries)
    queries.extend(generate_industry_queries(
        roles=roles,
        industries=industries,
        max_queries=industry_count,
    ))

    return queries[:max_queries]


def generate_queries(max_queries: int = 10) -> list[dict]:
    """
    Generate a balanced set of queries using default configuration.

    Returns list of query dicts with 'query', 'type', and 'metadata' keys.
    """
    queries = []

    # Mix of different query types
    queries.extend(generate_professional_queries(max_queries=int(max_queries * 0.5)))
    queries.extend(generate_recruiter_queries(max_queries=int(max_queries * 0.3)))
    queries.extend(generate_industry_queries(max_queries=int(max_queries * 0.2)))

    # Deduplicate by query string
    seen = set()
    unique_queries = []
    for q in queries:
        if q["query"] not in seen:
            seen.add(q["query"])
            unique_queries.append(q)

    return unique_queries[:max_queries]


if __name__ == "__main__":
    print("Sample Generated Queries:")
    print("-" * 50)

    queries = generate_queries(max_queries=10)
    for i, q in enumerate(queries, 1):
        print(f"\n{i}. [{q['type']}]")
        print(f"   Query: {q['query']}")
        print(f"   Metadata: {q['metadata']}")
