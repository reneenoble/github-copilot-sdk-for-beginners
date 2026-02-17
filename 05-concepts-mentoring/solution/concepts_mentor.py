"""
Chapter 5 — Extracting Concepts & Mentoring Advice: Solution
GitHub Copilot SDK for Beginners

Issue Reviewer that extracts required concepts and generates
difficulty-appropriate mentoring advice.
"""

import asyncio
import json
import os
from copilot import CopilotClient, define_tool
from pydantic import BaseModel, Field
from typing import Literal


# --- Pydantic Schema ---

class IssueReview(BaseModel):
    summary: str
    difficulty_score: int = Field(ge=1, le=5)
    recommended_level: Literal["Junior", "Mid", "Senior", "Senior+"]
    concepts_required: list[str] = Field(
        description="Specific technologies and skills needed"
    )
    mentoring_advice: str = Field(
        description="Actionable guidance tailored to difficulty level"
    )
    files_analyzed: list[str] = Field(default_factory=list)


# --- Tool Definition ---

class GetFileParams(BaseModel):
    file_path: str = Field(description="Relative path to the file")


@define_tool(description="Read the contents of a file from the repository")
async def get_file_contents(params: GetFileParams) -> str:
    repo_root = os.environ.get("REPO_PATH", ".")
    full_path = os.path.realpath(os.path.join(repo_root, params.file_path))
    if not full_path.startswith(os.path.realpath(repo_root)):
        return "Error: Access denied"
    try:
        with open(full_path, "r") as f:
            content = f.read()
            return content[:10_000] if len(content) > 10_000 else content
    except FileNotFoundError:
        return f"Error: File not found: {params.file_path}"


SYSTEM_PROMPT = """You are a GitHub issue reviewer and development mentor.

Analyze the issue and any referenced files, then respond with ONLY a JSON object:
{
  "summary": "<one sentence>",
  "difficulty_score": 1-5,
  "recommended_level": "Junior | Mid | Senior | Senior+",
  "concepts_required": ["<specific technology or skill>", ...],
  "mentoring_advice": "<guidance tailored to difficulty>",
  "files_analyzed": ["<files you read>"]
}

## Difficulty Rubric
Score 1 — Junior: Typos, docs, config. No logic changes.
Score 2 — Junior/Mid: Simple bug, single file, clear fix.
Score 3 — Mid: Feature in one subsystem, 2-5 files.
Score 4 — Senior: Cross-cutting concern (perf, security). Multiple subsystems.
Score 5 — Senior+: Architecture redesign, migration, breaking changes.

## Concepts Extraction
List specific technologies, patterns, and skills. Be precise:
- Good: "JWT token validation", "Python decorator pattern", "SQL injection prevention"
- Bad: "coding", "debugging", "programming" (too vague)

Aim for 3-8 concepts per issue.

## Mentoring Advice Rules
- Score 1-2: Step-by-step guidance. Explain concepts. Suggest learning resources.
  Use encouraging, supportive tone. E.g., "Great first issue! Start by..."
- Score 3: Outline the approach. Mention relevant patterns and considerations.
  Assume competence but provide direction.
- Score 4-5: High-level strategy. Discuss trade-offs and architecture impacts.
  Treat as a peer discussion. Address migration paths and risk areas."""


# --- Test Issues ---

EASY_ISSUE = """
Title: Fix typo in README.md

The word "authentication" is misspelled as "authentification" on line 42
of the README.md file.
"""

MEDIUM_ISSUE = """
Title: Add rate limiting to API endpoints

We're getting too many requests from some clients. Need to add rate
limiting to the API endpoints in src/routes/api.py. Should use a
sliding window approach and return 429 status codes.
"""

HARD_ISSUE = """
Title: Migrate authentication system from session-based to OAuth 2.0

We need to migrate our entire authentication system to OAuth 2.0 with
support for Google, GitHub, and Microsoft providers. This affects:
- src/auth/login.py (session handling → OAuth flow)
- src/auth/middleware.py (session checks → token validation)
- src/models/user.py (add OAuth fields)
- src/routes/callback.py (new file — OAuth callback handler)
- Database migration for OAuth tokens table
- All existing tests in tests/auth/
Must maintain backward compatibility during migration.
"""


async def review_issue(client, issue_text: str, label: str):
    """Review a single issue and display the results."""
    session = await client.create_session({
        "model": "gpt-4.1",
        "system_message": {
            "mode": "replace",
            "content": SYSTEM_PROMPT
        },
        "tools": [get_file_contents],
    })

    print(f"\n{'═' * 60}")
    print(f"📋 Reviewing: {label}")
    print(f"{'═' * 60}\n")

    response = await session.send_and_wait({"prompt": issue_text})

    try:
        review = IssueReview.model_validate_json(response.data.content)

        print(f"  📝 Summary: {review.summary}")
        print(f"  📊 Difficulty: {review.difficulty_score}/5 "
              f"({review.recommended_level})")
        print(f"  🧠 Concepts: {', '.join(review.concepts_required)}")
        if review.files_analyzed:
            print(f"  📂 Files read: {', '.join(review.files_analyzed)}")
        print(f"\n  💡 Mentoring Advice:")
        # Wrap advice text at ~70 chars for readability
        advice = review.mentoring_advice
        words = advice.split()
        line = "     "
        for word in words:
            if len(line) + len(word) + 1 > 75:
                print(line)
                line = "     " + word
            else:
                line += " " + word if line.strip() else "     " + word
        if line.strip():
            print(line)

    except Exception as e:
        print(f"  ⚠️ Could not parse response: {e}")
        print(f"  Raw: {response.data.content[:300]}")

    print()


async def main():
    client = CopilotClient()
    await client.start()

    # Review issues at different difficulty levels
    await review_issue(client, EASY_ISSUE, "Easy — Typo Fix")
    await review_issue(client, MEDIUM_ISSUE, "Medium — Rate Limiting")
    await review_issue(client, HARD_ISSUE, "Hard — OAuth Migration")

    await client.stop()


asyncio.run(main())
