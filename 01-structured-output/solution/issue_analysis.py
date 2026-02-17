"""
Chapter 1 — Structured Output: Solution
GitHub Copilot SDK for Beginners

Issue Reviewer that returns structured JSON output,
validated with Pydantic.
"""

import asyncio
import json
from copilot import CopilotClient
from pydantic import BaseModel, Field


class IssueAnalysis(BaseModel):
    """Schema for structured issue analysis output."""
    summary: str = Field(description="One-sentence summary of the issue")
    difficulty_score: int = Field(
        ge=1, le=5,
        description="Difficulty from 1 (trivial) to 5 (expert-level)"
    )
    recommended_level: str = Field(
        description="One of: Junior, Mid, Senior, Senior+"
    )


SYSTEM_PROMPT = """You are a GitHub issue analyzer. When given an issue, respond
with ONLY a JSON object (no markdown, no code fences, no extra text) matching
this exact schema:

{
  "summary": "One-sentence summary of the issue",
  "difficulty_score": 1-5,
  "recommended_level": "Junior | Mid | Senior | Senior+"
}

Rules:
- difficulty_score must be an integer from 1 to 5
- recommended_level must be exactly one of: Junior, Mid, Senior, Senior+
- summary must be a single sentence
- Return ONLY the JSON object, nothing else
"""

SAMPLE_ISSUE = """
Title: Database connection pool exhaustion under load

Our PostgreSQL connection pool runs out of connections during peak hours.
The app uses SQLAlchemy with a pool size of 10. Under load testing with
100 concurrent users, we see "QueuePool limit exceeded" errors after
about 2 minutes. Need to implement connection pooling with PgBouncer
or increase pool size with proper timeout handling.
"""


async def main():
    client = CopilotClient()
    await client.start()

    session = await client.create_session({
        "model": "gpt-4.1",
        "system_message": {
            "mode": "replace",
            "content": SYSTEM_PROMPT,
        }
    })

    response = await session.send_and_wait({
        "prompt": f"Analyze this GitHub issue:\n\n{SAMPLE_ISSUE}"
    })

    try:
        raw = response.data.content
        data = json.loads(raw)
        analysis = IssueAnalysis(**data)

        print(f"Summary:     {analysis.summary}")
        print(f"Difficulty:  {analysis.difficulty_score}/5")
        print(f"Level:       {analysis.recommended_level}")
    except json.JSONDecodeError:
        print("Error: Model did not return valid JSON")
        print(f"Raw response: {response.data.content}")
    except Exception as e:
        print(f"Validation error: {e}")

    await session.destroy()
    await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
