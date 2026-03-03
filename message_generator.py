"""
Message Generator - Uses Claude API to craft personalized outreach messages
"""

from typing import Optional

import anthropic
import pandas as pd

import config


def create_anthropic_client() -> anthropic.Anthropic:
    """Create Anthropic API client."""
    if config.ANTHROPIC_API_KEY == "YOUR_ANTHROPIC_API_KEY_HERE":
        raise ValueError(
            "Anthropic API key not configured. "
            "Please set ANTHROPIC_API_KEY in config.py. "
            "See config.py for setup instructions."
        )

    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


CONNECTION_MESSAGE_PROMPT = """You are a professional networking assistant. Write a brief, personalized LinkedIn connection request message from a job seeker to a potential contact.

Job Seeker Background:
{cv_summary}

Target Profile:
- Name: {name}
- Title: {profile_title}
- Company: {company}
- Location: {location}

Guidelines:
- Maximum 300 characters (LinkedIn connection request limit)
- Be concise and genuine
- Mention specific relevance to target's background if possible
- Include a clear but soft call-to-action
- No generic templates - make it personal
- Do not start with "Hi [Name]" - LinkedIn shows the name already
- Do not be overly formal or use cliches

Write ONLY the message text, nothing else."""


INMAIL_MESSAGE_PROMPT = """You are a professional networking assistant. Write a personalized LinkedIn InMail message from a job seeker to a potential contact.

Job Seeker Background:
{cv_summary}

Target Profile:
- Name: {name}
- Title: {profile_title}
- Company: {company}
- Location: {location}

Guidelines:
- Around 100-150 words
- Be genuine and professional
- Explain why you're reaching out to this specific person
- Briefly highlight relevant experience/skills
- Include a clear but respectful call-to-action
- No generic templates - make it personal
- Show you've done research on their background

Write ONLY the message text, nothing else."""


def generate_message(
    client: anthropic.Anthropic,
    prompt: str,
    cv_summary: str,
    profile: dict,
) -> str:
    """Generate a single message using Claude API."""
    formatted_prompt = prompt.format(
        cv_summary=cv_summary,
        name=profile.get("name", "Unknown"),
        profile_title=profile.get("profile_title", "Professional"),
        company=profile.get("company", ""),
        location=profile.get("location", ""),
    )

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[
            {"role": "user", "content": formatted_prompt}
        ],
    )

    return message.content[0].text.strip()


def generate_messages(
    cv_summary: str,
    profiles_path: Optional[str] = None,
    output_path: Optional[str] = None,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Generate personalized messages for profiles.

    Args:
        cv_summary: Summary of job seeker's CV
        profiles_path: Path to profile CSV (defaults to config.PROFILE_OUTPUT_PATH)
        output_path: Path to save output CSV (defaults to config.MESSAGE_OUTPUT_PATH)
        limit: Max number of profiles to process (None for all)

    Returns:
        DataFrame with profiles and generated messages
    """
    profiles_path = profiles_path or config.PROFILE_OUTPUT_PATH
    output_path = output_path or config.MESSAGE_OUTPUT_PATH

    # Load profiles
    try:
        df = pd.read_csv(profiles_path)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Profile file not found: {profiles_path}. "
            "Run 'python main.py find' first to generate profiles."
        )

    if df.empty:
        print("No profiles to process.")
        return df

    # Limit profiles if specified
    if limit:
        df = df.head(limit)

    print(f"Generating messages for {len(df)} profiles...")

    client = create_anthropic_client()

    connection_messages = []
    inmail_messages = []

    for i, (_, profile) in enumerate(df.iterrows(), 1):
        name = profile.get("name", "Unknown")
        print(f"  [{i}/{len(df)}] Processing: {name}...")

        try:
            # Generate connection message
            connection_msg = generate_message(
                client,
                CONNECTION_MESSAGE_PROMPT,
                cv_summary,
                profile.to_dict(),
            )
            connection_messages.append(connection_msg)

            # Generate InMail message
            inmail_msg = generate_message(
                client,
                INMAIL_MESSAGE_PROMPT,
                cv_summary,
                profile.to_dict(),
            )
            inmail_messages.append(inmail_msg)

            # Truncate connection message if too long
            if len(connection_msg) > 300:
                connection_messages[-1] = connection_msg[:297] + "..."

        except Exception as e:
            print(f"      Error generating message: {e}")
            connection_messages.append("")
            inmail_messages.append("")

    # Add messages to DataFrame
    df["connection_message"] = connection_messages
    df["inmail_message"] = inmail_messages

    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"\nSaved {len(df)} profiles with messages to {output_path}")

    return df


if __name__ == "__main__":
    # Test with sample data
    test_summary = "Product Manager with 5 years experience in e-commerce and fintech. Skills: SQL, Python, Agile, stakeholder management."

    print("Testing message generator...")

    try:
        df = generate_messages(cv_summary=test_summary, limit=1)
        if not df.empty:
            print("\nGenerated connection message:")
            print(df.iloc[0]["connection_message"])
            print("\nGenerated InMail message:")
            print(df.iloc[0]["inmail_message"])
    except FileNotFoundError as e:
        print(f"\nError: {e}")
    except ValueError as e:
        print(f"\nConfiguration error: {e}")
