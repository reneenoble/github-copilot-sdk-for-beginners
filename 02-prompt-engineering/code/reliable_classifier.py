"""
Chapter 2 — Prompt Engineering: Starter Code
GitHub Copilot SDK for Beginners

TODO: Add a rubric and few-shot examples for reliable classification.
"""

import asyncio
import json
from copilot import CopilotClient
from copilot.session import PermissionHandler
from copilot.generated.session_events import AssistantMessageData
from pydantic import BaseModel, Field


class IssueAnalysis(BaseModel):
    summary: str
    difficulty_score: int = Field(ge=1, le=5)
    recommended_level: str


# TODO 1: Replace this vague prompt with one that includes:
#   - A clear 5-level difficulty rubric
#   - At least 2 few-shot examples
#   - Explicit allowed values for recommended_level
SYSTEM_PROMPT = """Analyze GitHub issues and return JSON with
summary, difficulty_score, and recommended_level."""


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

    # TODO 2: Run the same issue 3 times and compare results
    # Are the scores consistent?

    session = await client.create_session(
        on_permission_request=PermissionHandler.approve_all,
        model="gpt-4.1",
        system_message={"mode": "replace", "content": SYSTEM_PROMPT},
    )

    response = await session.send_and_wait(f"Analyze:\n\n{SAMPLE_ISSUE}")

    try:
        if not response or not isinstance(response.data, AssistantMessageData):
            print("No response received")
        else:
            data = json.loads(response.data.content)
            analysis = IssueAnalysis(**data)
            print(f"Summary:    {analysis.summary}")
            print(f"Difficulty: {analysis.difficulty_score}/5")
            print(f"Level:      {analysis.recommended_level}")
    except Exception as e:
        print(f"Error: {e}")

    await session.disconnect()
    await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
