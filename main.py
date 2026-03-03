#!/usr/bin/env python3
"""
ProspectFinder - LinkedIn prospect finder and cold outreach message generator

Usage:
    python main.py find [--queries N] [--cv PATH]
    python main.py generate [--limit N]
    python main.py run [--queries N] [--cv PATH] [--limit N]
"""

import argparse
import sys

import config
from cv_parser import parse_cv
from query_generator import generate_queries, generate_queries_from_cv
from profile_finder import find_profiles
from message_generator import generate_messages


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

    # Generate queries
    print(f"\nGenerating {args.queries} search queries...")
    if cv_data:
        queries = generate_queries_from_cv(cv_data, max_queries=args.queries)
    else:
        queries = generate_queries(max_queries=args.queries)
    print(f"  Generated {len(queries)} queries")

    # Execute searches
    print("\nSearching for profiles...")
    try:
        df = find_profiles(queries, cv_keywords=cv_keywords)
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
  python main.py find                    # Find profiles with default settings
  python main.py find --queries 5        # Find profiles with 5 queries
  python main.py generate                # Generate messages for found profiles
  python main.py generate --limit 10     # Generate messages for top 10 profiles
  python main.py run                     # Run full pipeline

Before running, configure your API keys in config.py:
  - GOOGLE_API_KEY: Google Cloud API key
  - GOOGLE_CSE_ID: Custom Search Engine ID
  - ANTHROPIC_API_KEY: Anthropic API key
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Find command
    find_parser = subparsers.add_parser("find", help="Find LinkedIn profiles")
    find_parser.add_argument(
        "--queries", "-q",
        type=int,
        default=config.DEFAULT_QUERIES_COUNT,
        help=f"Number of search queries to run (default: {config.DEFAULT_QUERIES_COUNT})",
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

    if args.command == "find":
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
