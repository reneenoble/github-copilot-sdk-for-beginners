"""
Chapter 5 — Extracting Concepts & Mentoring Advice: Starter Code
GitHub Copilot SDK for Beginners

Expand the Issue Reviewer to extract required concepts and generate
mentoring advice tailored to the issue's difficulty level.
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
    # TODO 1: Add a 'concepts_required' field — a list of strings
    #   for the specific technologies and skills needed
    # TODO 2: Add a 'mentoring_advice' field — a string with
    #   guidance tailored to the difficulty level
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


# TODO 3: Write a SYSTEM_PROMPT that includes:
#   - A difficulty rubric (Score 1-5 with descriptions)
#   - Concept extraction rules (precise, not vague)
#   - Mentoring advice rules (different tone per difficulty tier)
#   - Instruction to respond with ONLY a JSON object matching the schema
SYSTEM_PROMPT = """"""


# --- Test Issues ---

EASY_ISSUE = """
Title: Fix typo in README.md

The word "authentication" is misspelled as "authentification" on line 42.
"""

HARD_ISSUE = """
Title: Migrate authentication system from session-based to OAuth 2.0

We need to migrate our entire authentication system to OAuth 2.0 with
support for Google, GitHub, and Microsoft providers. This affects:
- src/auth/login.py
- src/auth/middleware.py
- src/models/user.py
- src/routes/callback.py (new file)
- Database migration
Must maintain backward compatibility during migration.
"""


async def review_issue(client, issue_text: str, label: str):
    """Review a single issue and display results."""
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

    # TODO 4: Parse the JSON response into an IssueReview model.
    #   Print cada field: summary, difficulty, concepts, mentoring advice.
    #   Handle parsing errors gracefully.
    print(response.data.content)


async def main():
    client = CopilotClient()
    await client.start()

    # TODO 5: Review both issues and compare the mentoring styles
    await review_issue(client, EASY_ISSUE, "Easy Issue")
    await review_issue(client, HARD_ISSUE, "Hard Issue")

    await client.stop()


asyncio.run(main())
