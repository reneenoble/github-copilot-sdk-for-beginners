"""
Chapter 8 — Evaluation & Testing: Solution
GitHub Copilot SDK for Beginners

Complete test harness that measures accuracy, consistency, and schema validity
of the Issue Reviewer.
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
Score 4 — Senior: Cross-cutting concern (perf, security). Multiple subsystems.
Score 5 — Senior+: Architecture redesign, migration, breaking changes.

## Concepts Extraction
Be specific: "JWT validation", not "security".

## Mentoring Advice
Score 1-2: Step-by-step. Score 3: Outline approach. Score 4-5: Strategy."""


# --- Golden Test Cases ---

GOLDEN_TESTS = [
    {
        "name": "Typo fix",
        "issue": (
            "Title: Fix typo in README\n\n"
            "The word 'recieve' should be 'receive' on line 42 of README.md."
        ),
        "expected_score": 1,
        "expected_level": "Junior",
    },
    {
        "name": "Simple bug",
        "issue": (
            "Title: Fix off-by-one error\n\n"
            "The loop in src/utils.py uses `range(len(items))` but accesses "
            "`items[i+1]`, causing an IndexError on the last iteration."
        ),
        "expected_score": 2,
        "expected_level": "Junior",
    },
    {
        "name": "New feature",
        "issue": (
            "Title: Add pagination to user list endpoint\n\n"
            "The GET /users endpoint returns all users at once. "
            "Add limit/offset pagination with Link headers. "
            "Affects src/routes/users.py and src/models/user.py."
        ),
        "expected_score": 3,
        "expected_level": "Mid",
    },
    {
        "name": "Security vulnerability",
        "issue": (
            "Title: SQL injection in search endpoint\n\n"
            "The search endpoint in src/routes/search.py passes user input "
            "directly into a raw SQL query. Need parameterized queries, "
            "input validation, and audit logging across the search module."
        ),
        "expected_score": 4,
        "expected_level": "Senior",
    },
    {
        "name": "Architecture migration",
        "issue": (
            "Title: Migrate from monolith to microservices\n\n"
            "Decompose the monolithic application into microservices. "
            "This affects every module, the shared database (needs splitting), "
            "deployment pipelines, CI/CD, inter-service communication, "
            "and requires a phased migration plan with backward compatibility."
        ),
        "expected_score": 5,
        "expected_level": "Senior+",
    },
]


# --- Test Runner ---

async def run_review(client, issue_text: str) -> IssueReview | None:
    """Run a single review and return the parsed result."""
    session = await client.create_session({
        "model": "gpt-4.1",
        "system_message": {"mode": "replace", "content": SYSTEM_PROMPT},
    })

    response = await session.send_and_wait({"prompt": issue_text})

    content = response.data.content.strip()
    # Strip markdown code fences
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
    if content.endswith("```"):
        content = content.rsplit("```", 1)[0]
    content = content.strip()

    try:
        return IssueReview.model_validate_json(content)
    except (ValidationError, json.JSONDecodeError):
        return None


# --- Accuracy Tests ---

async def run_accuracy_tests(client):
    """Run all golden tests and report accuracy."""
    print("📊 ACCURACY TESTS")
    print("=" * 60)

    exact_matches = 0
    close_matches = 0
    level_matches = 0
    schema_valid = 0
    total = len(GOLDEN_TESTS)

    for test in GOLDEN_TESTS:
        review = await run_review(client, test["issue"])

        if review is None:
            print(f"  ❌ {test['name']}: Schema validation FAILED")
            continue

        schema_valid += 1

        score_exact = review.difficulty_score == test["expected_score"]
        score_close = abs(review.difficulty_score - test["expected_score"]) <= 1
        level_match = review.recommended_level == test["expected_level"]

        if score_exact:
            exact_matches += 1
        if score_close:
            close_matches += 1
        if level_match:
            level_matches += 1

        icon = "✅" if score_exact and level_match else (
            "⚠️" if score_close else "❌"
        )
        print(
            f"  {icon} {test['name']}: "
            f"Score {review.difficulty_score} "
            f"(expected {test['expected_score']}), "
            f"Level: {review.recommended_level} "
            f"(expected {test['expected_level']})"
        )

    print(f"\n  Schema valid:   {schema_valid}/{total}")
    print(f"  Exact score:    {exact_matches}/{total} "
          f"({exact_matches / total * 100:.0f}%)")
    print(f"  Close score ±1: {close_matches}/{total} "
          f"({close_matches / total * 100:.0f}%)")
    print(f"  Level match:    {level_matches}/{total} "
          f"({level_matches / total * 100:.0f}%)")
    print()


# --- Consistency Tests ---

async def run_consistency_tests(client, runs: int = 3):
    """Run a subset of tests multiple times to check consistency."""
    print("🔄 CONSISTENCY TESTS")
    print("=" * 60)

    # Test the easiest and hardest cases
    test_cases = [GOLDEN_TESTS[0], GOLDEN_TESTS[-1]]

    for test in test_cases:
        scores = []
        levels = []

        for i in range(runs):
            review = await run_review(client, test["issue"])
            if review:
                scores.append(review.difficulty_score)
                levels.append(review.recommended_level)
            else:
                scores.append(None)
                levels.append(None)

        valid_scores = [s for s in scores if s is not None]
        valid_levels = [l for l in levels if l is not None]

        score_consistent = len(set(valid_scores)) <= 1
        level_consistent = len(set(valid_levels)) <= 1
        icon = "✅" if score_consistent and level_consistent else "⚠️"

        print(f"  {icon} {test['name']}:")
        print(f"     Scores: {scores} "
              f"({'consistent' if score_consistent else 'INCONSISTENT'})")
        print(f"     Levels: {levels} "
              f"({'consistent' if level_consistent else 'INCONSISTENT'})")

    print()


# --- Concept Quality Check ---

async def run_concept_quality_tests(client):
    """Check that extracted concepts are specific, not vague."""
    print("🧠 CONCEPT QUALITY TESTS")
    print("=" * 60)

    vague_terms = {"coding", "programming", "debugging", "software",
                   "development", "technology", "engineering"}

    for test in GOLDEN_TESTS[:3]:
        review = await run_review(client, test["issue"])
        if not review:
            print(f"  ❌ {test['name']}: Failed to parse")
            continue

        vague_found = [c for c in review.concepts_required
                       if c.lower() in vague_terms]

        if vague_found:
            print(f"  ⚠️ {test['name']}: Vague concepts: {vague_found}")
        else:
            print(f"  ✅ {test['name']}: "
                  f"Concepts: {', '.join(review.concepts_required)}")

    print()


# --- Main ---

async def main():
    client = CopilotClient()
    await client.start()

    start = time.time()

    await run_accuracy_tests(client)
    await run_consistency_tests(client)
    await run_concept_quality_tests(client)

    elapsed = time.time() - start
    print(f"{'─' * 60}")
    print(f"⏱️  Total time: {elapsed:.1f}s")
    print(f"{'─' * 60}")

    await client.stop()


asyncio.run(main())
