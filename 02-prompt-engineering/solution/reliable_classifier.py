"""
Chapter 2 — Prompt Engineering: Solution
GitHub Copilot SDK for Beginners

A reliable issue classifier with rubric and few-shot examples.
"""

import asyncio
import json
from copilot import CopilotClient
from pydantic import BaseModel, Field


class IssueAnalysis(BaseModel):
    summary: str
    difficulty_score: int = Field(ge=1, le=5)
    recommended_level: str


RUBRIC_PROMPT = """You are a GitHub issue difficulty classifier. You MUST respond
with ONLY a valid JSON object (no markdown, no code fences, no extra text).

## Difficulty Rubric

Score 1 — Junior: Typos, documentation, config changes. No logic changes needed.
Score 2 — Junior/Mid: Simple bug fix with clear error message. Single file, <20 lines changed.
Score 3 — Mid: Feature work in one subsystem. Requires understanding of 2-5 files.
  Moderate domain knowledge needed.
Score 4 — Senior: Cross-cutting concerns (performance, security, API design).
  Multiple subsystems affected. Requires architectural understanding.
Score 5 — Senior+: Architecture redesign, data migration, backward compatibility.
  System-wide impact with risk of regressions.

## Required Output Format

{
  "summary": "<one sentence>",
  "difficulty_score": <1-5 integer, strictly based on rubric above>,
  "recommended_level": "<EXACTLY one of: Junior, Mid, Senior, Senior+>"
}

## Level Mapping
- Scores 1-2 → "Junior"
- Score 3 → "Mid"
- Score 4 → "Senior"
- Score 5 → "Senior+"

## Rules
- Apply the rubric strictly
- recommended_level MUST be exactly one of: Junior, Mid, Senior, Senior+
- Do NOT use values like "Intermediate", "Beginner", "Expert", etc.
- Return ONLY the JSON object

## Examples

Issue: "Fix typo: 'recieve' → 'receive' in login form label"
{"summary": "Fix typo in login form label", "difficulty_score": 1, "recommended_level": "Junior"}

Issue: "Implement distributed rate limiting with Redis across multiple server instances,
including graceful degradation when Redis is unavailable"
{"summary": "Add Redis-based distributed rate limiting with failover", "difficulty_score": 4, "recommended_level": "Senior"}

Issue: "Add unit tests for the validateEmail utility function"
{"summary": "Add unit tests for email validation utility", "difficulty_score": 2, "recommended_level": "Junior"}
"""


SAMPLE_ISSUE = """
Title: Add pagination to the /api/users endpoint

The /api/users endpoint currently returns all users in a single response.
With 50,000+ users in production, this causes timeouts and excessive memory
usage. Need to add cursor-based pagination with configurable page size.
Should also update the API documentation and add pagination to the
frontend user list component.
"""


async def main():
    client = CopilotClient()
    await client.start()

    print("=== Consistency Test: 3 runs of the same issue ===\n")

    for i in range(3):
        session = await client.create_session({
            "model": "gpt-4.1",
            "system_message": {"mode": "replace", "content": RUBRIC_PROMPT},
        })

        response = await session.send_and_wait({
            "prompt": f"Analyze:\n\n{SAMPLE_ISSUE}"
        })

        try:
            data = json.loads(response.data.content)
            analysis = IssueAnalysis(**data)
            print(f"Run {i+1}: score={analysis.difficulty_score}, "
                  f"level={analysis.recommended_level}, "
                  f"summary={analysis.summary}")
        except Exception as e:
            print(f"Run {i+1}: Error — {e}")

        await session.destroy()

    await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
