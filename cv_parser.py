"""
CV Parser - Extracts and structures text from PDF resumes
"""

import re
from pathlib import Path

import pdfplumber


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_skills(text: str) -> list[str]:
    """Extract skills from CV text using common patterns."""
    skills = []

    # Common skill keywords to look for
    skill_patterns = [
        r"(?:skills?|expertise|proficient in|experience with)[:\s]*([^\n]+)",
        r"(?:technologies|tools|languages)[:\s]*([^\n]+)",
    ]

    for pattern in skill_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Split by common delimiters
            items = re.split(r"[,;|•·]", match)
            skills.extend([s.strip() for s in items if s.strip()])

    # Also extract common tech keywords
    tech_keywords = [
        "Python", "Java", "JavaScript", "SQL", "Excel", "Tableau", "Power BI",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "React", "Node.js",
        "Machine Learning", "Data Science", "Analytics", "Agile", "Scrum",
        "Product Management", "Project Management", "Business Analysis",
    ]

    text_lower = text.lower()
    for keyword in tech_keywords:
        if keyword.lower() in text_lower and keyword not in skills:
            skills.append(keyword)

    return list(set(skills))


def extract_experience(text: str) -> list[dict]:
    """Extract work experience entries from CV text."""
    experiences = []

    # Look for common experience section headers
    exp_section_pattern = r"(?:experience|employment|work history)[:\s]*\n([\s\S]*?)(?=\n(?:education|skills|certifications|projects)|$)"
    exp_match = re.search(exp_section_pattern, text, re.IGNORECASE)

    if exp_match:
        exp_text = exp_match.group(1)

        # Try to find job entries (company, title, dates)
        job_pattern = r"([A-Z][^\n]+)\n([^\n]+)\n?.*?(\d{4}[^\n]*\d{4}|\d{4}[^\n]*present)"
        jobs = re.findall(job_pattern, exp_text, re.IGNORECASE)

        for job in jobs:
            experiences.append({
                "company": job[0].strip(),
                "title": job[1].strip(),
                "dates": job[2].strip() if len(job) > 2 else "",
            })

    return experiences


def extract_education(text: str) -> list[dict]:
    """Extract education entries from CV text."""
    education = []

    # Look for education section
    edu_section_pattern = r"(?:education|academic|qualifications)[:\s]*\n([\s\S]*?)(?=\n(?:experience|skills|certifications|projects)|$)"
    edu_match = re.search(edu_section_pattern, text, re.IGNORECASE)

    if edu_match:
        edu_text = edu_match.group(1)

        # Look for degree patterns
        degree_patterns = [
            r"((?:Bachelor|Master|MBA|PhD|B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?)[^\n]*)",
        ]

        for pattern in degree_patterns:
            matches = re.findall(pattern, edu_text, re.IGNORECASE)
            for match in matches:
                education.append({"degree": match.strip()})

    return education


def extract_keywords(text: str) -> list[str]:
    """Extract important keywords for matching purposes."""
    # Common industry and role keywords
    keywords = []

    keyword_list = [
        # Industries
        "technology", "fintech", "e-commerce", "logistics", "FMCG",
        "healthcare", "finance", "banking", "consulting", "retail",
        "manufacturing", "telecommunications", "media", "entertainment",
        # Roles
        "product manager", "data analyst", "business analyst", "project manager",
        "software engineer", "data scientist", "UX designer", "marketing",
        # Seniority
        "senior", "lead", "head", "manager", "director", "VP", "chief",
        # Locations
        "Indonesia", "Jakarta", "Singapore", "Malaysia", "Thailand",
        "Vietnam", "Philippines", "APAC", "Asia Pacific",
    ]

    text_lower = text.lower()
    for keyword in keyword_list:
        if keyword.lower() in text_lower:
            keywords.append(keyword)

    return list(set(keywords))


def parse_cv(pdf_path: str) -> dict:
    """
    Parse a CV PDF and return structured data.

    Returns:
        dict with keys:
        - raw_text: Full extracted text
        - skills: List of identified skills
        - experience: List of work experience entries
        - education: List of education entries
        - keywords: Important keywords for matching
        - summary: Brief text summary for prompts
    """
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"CV file not found: {pdf_path}")

    raw_text = extract_text_from_pdf(pdf_path)

    if not raw_text.strip():
        raise ValueError(f"Could not extract text from PDF: {pdf_path}")

    skills = extract_skills(raw_text)
    experience = extract_experience(raw_text)
    education = extract_education(raw_text)
    keywords = extract_keywords(raw_text)

    # Create a summary for use in prompts
    summary_parts = []
    if skills:
        summary_parts.append(f"Skills: {', '.join(skills[:10])}")
    if experience:
        recent = experience[0] if experience else {}
        if recent:
            summary_parts.append(f"Recent role: {recent.get('title', '')} at {recent.get('company', '')}")
    if education:
        summary_parts.append(f"Education: {education[0].get('degree', '')}")

    summary = ". ".join(summary_parts) if summary_parts else raw_text[:500]

    return {
        "raw_text": raw_text,
        "skills": skills,
        "experience": experience,
        "education": education,
        "keywords": keywords,
        "summary": summary,
    }


if __name__ == "__main__":
    import sys

    cv_path = sys.argv[1] if len(sys.argv) > 1 else "CV.pdf"

    try:
        result = parse_cv(cv_path)
        print("CV Parsed Successfully!")
        print(f"\nSkills found: {len(result['skills'])}")
        print(f"Experience entries: {len(result['experience'])}")
        print(f"Education entries: {len(result['education'])}")
        print(f"Keywords: {len(result['keywords'])}")
        print(f"\nSummary:\n{result['summary']}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")
