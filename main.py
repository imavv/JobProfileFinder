#!/usr/bin/env python3
"""
ProspectFinder - LinkedIn prospect finder and cold outreach message generator

Usage:
    python main.py find [--queries N] [--cv PATH]
    python main.py find --query-file queries/ranked_queries.csv --top 10
    python main.py generate [--limit N]
    python main.py run [--queries N] [--cv PATH] [--limit N]
    python main.py query-rank --params queries/query_params.txt --cv CV.pdf
    python main.py query-cv --cv CV.pdf
"""

import argparse
import sys

import config
from cv_parser import parse_cv
from query_generator import (
    generate_queries,
    generate_queries_from_cv,
    parse_query_params,
    generate_permutations,
    rank_queries_by_cv,
    save_ranked_queries_csv,
    generate_cv_specific_queries,
    generate_cv_broad_queries,
    save_cv_queries_csv,
)
from profile_finder import find_profiles, load_queries_from_csv
from message_generator import generate_messages


def cmd_query_rank(args):
    """Generate and rank query permutations by CV similarity."""
    print("=" * 50)
    print("ProspectFinder - Query Ranking")
    print("=" * 50)

    print(f"\nParsing params file: {args.params}")
    params = parse_query_params(args.params)
    print(f"  Locations: {len(params.get('locations', []))} items")
    print(f"  Seniorities: {len(params.get('seniority', []))} items")
    print(f"  Roles: {len(params.get('roles', []))} items")

    print("\nGenerating permutations...")
    queries = generate_permutations(params)
    print(f"  Generated {len(queries)} query combinations")

    print(f"\nRanking queries against CV: {args.cv}")
    ranked = rank_queries_by_cv(queries, args.cv)

    output_path = args.output or config.RANKED_QUERIES_PATH
    save_ranked_queries_csv(ranked, output_path)

    print(f"\nTop 5 queries by CV similarity:")
    for r in ranked[:5]:
        print(f"  {r['rank']}. (score: {r['similarity_score']:.4f}) {r['query'][:60]}...")

    return ranked


def cmd_query_cv(args):
    """Generate queries directly from CV content."""
    print("=" * 50)
    print("ProspectFinder - CV Query Generation")
    print("=" * 50)

    print(f"\nParsing CV: {args.cv}")
    cv_data = parse_cv(args.cv)
    print(f"  Skills found: {len(cv_data.get('skills', []))}")
    print(f"  Experience entries: {len(cv_data.get('experience', []))}")
    print(f"  Keywords: {len(cv_data.get('keywords', []))}")

    print(f"\nGenerating highly specific queries (limit: {args.specific})...")
    specific_queries = generate_cv_specific_queries(cv_data, count=args.specific)
    print(f"  Generated {len(specific_queries)} highly specific queries")

    print(f"\nGenerating broadly similar queries (limit: {args.broad})...")
    broad_queries = generate_cv_broad_queries(cv_data, count=args.broad)
    print(f"  Generated {len(broad_queries)} broadly similar queries")

    all_queries = specific_queries + broad_queries

    output_path = args.output or config.CV_QUERIES_PATH
    save_cv_queries_csv(all_queries, output_path)

    print(f"\nGenerated queries:")
    for q in all_queries:
        print(f"  [{q['category']}] {q['query']}")

    return all_queries


def cmd_find(args):
    """Find LinkedIn profiles using X-ray search."""
    print("=" * 50)
    print("ProspectFinder - Profile Search")
    print("=" * 50)

    # Parse CV if available
    cv_data = None
    cv_keywords = []

    try:
        print(f"\nParsing CV: {args.cv}")
        cv_data = parse_cv(args.cv)
        cv_keywords = cv_data.get("keywords", []) + cv_data.get("skills", [])
        print(f"  Found {len(cv_keywords)} keywords for matching")
    except FileNotFoundError:
        print(f"  CV file not found: {args.cv}")
        print("  Proceeding without CV-based matching...")
    except Exception as e:
        print(f"  Error parsing CV: {e}")
        print("  Proceeding without CV-based matching...")

    # Generate or load queries
    if args.query_file:
        print(f"\nLoading queries from: {args.query_file}")
        queries = load_queries_from_csv(args.query_file, top_n=args.top)
        print(f"  Loaded {len(queries)} queries")
    elif args.query:
        queries = [{"query": args.query, "type": "custom", "metadata": {}}]
        print(f"\nUsing custom query: {args.query}")
    else:
        print(f"\nGenerating {args.queries} search queries...")
        if cv_data:
            queries = generate_queries_from_cv(cv_data, max_queries=args.queries)
        else:
            queries = generate_queries(max_queries=args.queries)
        print(f"  Generated {len(queries)} queries")

    # Execute searches
    print("\nSearching for profiles...")
    try:
        df = find_profiles(queries, cv_keywords=cv_keywords, results_per_query=args.results)
        if not df.empty:
            print(f"\nTop 10 profiles by match score:")
            print(df.head(10)[["name", "profile_title", "match_score"]].to_string(index=False))
        return df
    except ValueError as e:
        print(f"\nError: {e}")
        sys.exit(1)


def cmd_generate(args):
    """Generate personalized messages for found profiles."""
    print("=" * 50)
    print("ProspectFinder - Message Generation")
    print("=" * 50)

    # Parse CV for summary
    cv_summary = ""
    try:
        print(f"\nParsing CV: {args.cv}")
        cv_data = parse_cv(args.cv)
        cv_summary = cv_data.get("summary", "")
        print(f"  CV summary extracted ({len(cv_summary)} chars)")
    except FileNotFoundError:
        print(f"  CV file not found: {args.cv}")
        cv_summary = "Job seeker looking for new opportunities."
        print(f"  Using default summary")
    except Exception as e:
        print(f"  Error parsing CV: {e}")
        cv_summary = "Job seeker looking for new opportunities."
        print(f"  Using default summary")

    # Generate messages
    print("\nGenerating personalized messages...")
    try:
        df = generate_messages(
            cv_summary=cv_summary,
            limit=args.limit if args.limit else None,
        )
        if not df.empty:
            print(f"\nSample connection message:")
            print("-" * 40)
            print(df.iloc[0]["connection_message"])
        return df
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\nError: {e}")
        sys.exit(1)


def cmd_run(args):
    """Run full pipeline: find profiles then generate messages."""
    print("=" * 50)
    print("ProspectFinder - Full Pipeline")
    print("=" * 50)

    # Step 1: Find profiles
    df = cmd_find(args)
    if df is None or df.empty:
        print("\nNo profiles found. Stopping.")
        return

    # Step 2: Generate messages
    print("\n")
    cmd_generate(args)


def main():
    parser = argparse.ArgumentParser(
        description="ProspectFinder - LinkedIn prospect finder and message generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query generation
  python main.py query-rank --params queries/query_params.txt --cv CV.pdf
  python main.py query-cv --cv CV.pdf --specific 5 --broad 5

  # Profile search
  python main.py find                    # Find profiles with default settings
  python main.py find --queries 5        # Find profiles with 5 queries
  python main.py find --query-file queries/ranked_queries.csv --top 10
  python main.py find --query 'site:linkedin.com/in "recruiter" "Singapore"'

  # Message generation
  python main.py generate                # Generate messages for found profiles
  python main.py generate --limit 10     # Generate messages for top 10 profiles
  python main.py run                     # Run full pipeline

Before running, configure your API keys in config.py:
  - SERPER_API_KEY: Serper.dev API key
  - ANTHROPIC_API_KEY: Anthropic API key
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Query-rank command
    query_rank_parser = subparsers.add_parser(
        "query-rank",
        help="Generate and rank query permutations by CV similarity",
    )
    query_rank_parser.add_argument(
        "--params", "-p",
        type=str,
        default=config.QUERY_PARAMS_PATH,
        help=f"Path to query params file (default: {config.QUERY_PARAMS_PATH})",
    )
    query_rank_parser.add_argument(
        "--cv",
        type=str,
        default=config.CV_PATH,
        help=f"Path to CV PDF file (default: {config.CV_PATH})",
    )
    query_rank_parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help=f"Output CSV path (default: {config.RANKED_QUERIES_PATH})",
    )

    # Query-cv command
    query_cv_parser = subparsers.add_parser(
        "query-cv",
        help="Generate queries directly from CV content",
    )
    query_cv_parser.add_argument(
        "--cv",
        type=str,
        default=config.CV_PATH,
        help=f"Path to CV PDF file (default: {config.CV_PATH})",
    )
    query_cv_parser.add_argument(
        "--specific",
        type=int,
        default=5,
        help="Number of highly specific queries to generate (default: 5)",
    )
    query_cv_parser.add_argument(
        "--broad",
        type=int,
        default=5,
        help="Number of broadly similar queries to generate (default: 5)",
    )
    query_cv_parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help=f"Output CSV path (default: {config.CV_QUERIES_PATH})",
    )

    # Find command
    find_parser = subparsers.add_parser("find", help="Find LinkedIn profiles")
    find_parser.add_argument(
        "--queries", "-q",
        type=int,
        default=config.DEFAULT_QUERIES_COUNT,
        help=f"Number of search queries to run (default: {config.DEFAULT_QUERIES_COUNT})",
    )
    find_parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Custom X-ray query (overrides --queries). Example: 'site:linkedin.com/in \"product manager\" \"Jakarta\"'",
    )
    find_parser.add_argument(
        "--query-file",
        type=str,
        default=None,
        help="Load queries from CSV file (queries/ranked_queries.csv or queries/cv_queries.csv)",
    )
    find_parser.add_argument(
        "--top",
        type=int,
        default=None,
        help="Use only top N queries from query file (default: all)",
    )
    find_parser.add_argument(
        "--results",
        type=int,
        default=config.RESULTS_PER_QUERY,
        help=f"Results per query (default: {config.RESULTS_PER_QUERY})",
    )
    find_parser.add_argument(
        "--cv",
        type=str,
        default=config.CV_PATH,
        help=f"Path to CV PDF file (default: {config.CV_PATH})",
    )

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate outreach messages")
    gen_parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Limit number of profiles to process (default: all)",
    )
    gen_parser.add_argument(
        "--cv",
        type=str,
        default=config.CV_PATH,
        help=f"Path to CV PDF file (default: {config.CV_PATH})",
    )

    # Run command (full pipeline)
    run_parser = subparsers.add_parser("run", help="Run full pipeline (find + generate)")
    run_parser.add_argument(
        "--queries", "-q",
        type=int,
        default=config.DEFAULT_QUERIES_COUNT,
        help=f"Number of search queries to run (default: {config.DEFAULT_QUERIES_COUNT})",
    )
    run_parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Custom X-ray query (overrides --queries). Example: 'site:linkedin.com/in \"product manager\" \"Jakarta\"'",
    )
    run_parser.add_argument(
        "--query-file",
        type=str,
        default=None,
        help="Load queries from CSV file",
    )
    run_parser.add_argument(
        "--top",
        type=int,
        default=None,
        help="Use only top N queries from query file",
    )
    run_parser.add_argument(
        "--results",
        type=int,
        default=config.RESULTS_PER_QUERY,
        help=f"Results per query (default: {config.RESULTS_PER_QUERY})",
    )
    run_parser.add_argument(
        "--cv",
        type=str,
        default=config.CV_PATH,
        help=f"Path to CV PDF file (default: {config.CV_PATH})",
    )
    run_parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Limit number of profiles for message generation (default: all)",
    )

    args = parser.parse_args()

    if args.command == "query-rank":
        cmd_query_rank(args)
    elif args.command == "query-cv":
        cmd_query_cv(args)
    elif args.command == "find":
        cmd_find(args)
    elif args.command == "generate":
        cmd_generate(args)
    elif args.command == "run":
        cmd_run(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
