"""
Chapter 8 — Evaluation & Testing: Starter Code
GitHub Copilot SDK for Beginners

Build a test harness to measure accuracy, consistency, and schema validity.
"""

import asyncio
import json
import time
from copilot import CopilotClient
from pydantic import BaseModel, Field, ValidationError
from typing import Literal


# --- Schema ---

class IssueReview(BaseModel):
    summary: str
    difficulty_score: int = Field(ge=1, le=5)
    recommended_level: Literal["Junior", "Mid", "Senior", "Senior+"]
    concepts_required: list[str]
    mentoring_advice: str


SYSTEM_PROMPT = """You are a GitHub issue reviewer.

Respond with ONLY a JSON object:
{
  "summary": "<one sentence>",
  "difficulty_score": 1-5,
  "recommended_level": "Junior | Mid | Senior | Senior+",
  "concepts_required": ["<specific skill>", ...],
  "mentoring_advice": "<guidance>"
}

## Difficulty Rubric
Score 1 — Junior: Typos, docs, config. No logic changes.
Score 2 — Junior/Mid: Simple bug, single file, clear fix.
Score 3 — Mid: Feature in one subsystem, 2-5 files.
Score 4 — Senior: Cross-cutting (perf, security). Multiple subsystems.
Score 5 — Senior+: Architecture redesign, migration, breaking changes."""


# --- Golden Test Cases ---

# TODO 1: Define at least 5 golden test cases.
# Each should have: name, issue, expected_score, expected_level
# Cover all difficulty levels from 1 to 5.
GOLDEN_TESTS = [
    # {
    #     "name": "...",
    #     "issue": "Title: ...\n\n...",
    #     "expected_score": 1,
    #     "expected_level": "Junior",
    # },
]


async def run_review(client, issue_text: str) -> IssueReview | None:
    """Run a single review and return the parsed result."""
    # TODO 2: Create a session, send the issue, parse the response.
    #   - Create session with SYSTEM_PROMPT
    #   - Call send_and_wait with the issue text
    #   - Strip markdown code fences if present
    #   - Parse JSON into IssueReview
    #   - Return IssueReview or None on failure
    return None


async def run_accuracy_tests(client):
    """Run all golden tests and report accuracy."""
    print("📊 ACCURACY TESTS")
    print("=" * 60)

    # TODO 3: For each golden test:
    #   - Call run_review
    #   - Compare difficulty_score with expected_score (exact and ±1)
    #   - Compare recommended_level with expected_level
    #   - Print pass/fail for each test
    #   - Print summary: schema valid, exact match %, close match %

    for test in GOLDEN_TESTS:
        review = await run_review(client, test["issue"])
        if review:
            print(f"  {test['name']}: Score {review.difficulty_score}")
        else:
            print(f"  {test['name']}: FAILED to parse")

    print()


async def run_consistency_tests(client, runs: int = 3):
    """Run a subset of tests multiple times to check consistency."""
    print("🔄 CONSISTENCY TESTS")
    print("=" * 60)

    # TODO 4: Pick 2 test cases (easy and hard).
    #   Run each 'runs' times. Collect scores and levels.
    #   Report whether results are consistent across runs.

    print("  (not implemented yet)")
    print()


async def main():
    client = CopilotClient()
    await client.start()

    start = time.time()

    await run_accuracy_tests(client)
    await run_consistency_tests(client)

    elapsed = time.time() - start
    print(f"⏱️  Total time: {elapsed:.1f}s")

    await client.stop()


asyncio.run(main())
