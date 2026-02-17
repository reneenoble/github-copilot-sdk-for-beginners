"""
Chapter 1 — Structured Output: Starter Code
GitHub Copilot SDK for Beginners

TODO: Complete this script to return structured JSON output from the model.
"""

import asyncio
import json
from copilot import CopilotClient
from pydantic import BaseModel, Field


# TODO 1: Define a Pydantic model called IssueAnalysis with:
#   - summary: str
#   - difficulty_score: int (1-5)
#   - recommended_level: str ("Junior", "Mid", "Senior", "Senior+")


# TODO 2: Write a system prompt that instructs the model to return ONLY
# a JSON object matching your schema
SYSTEM_PROMPT = """
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

    # TODO 3: Create a session with the system message
    session = await client.create_session({
        "model": "gpt-4.1",
        # Add system_message here
    })

    response = await session.send_and_wait({
        "prompt": f"Analyze this GitHub issue:\n\n{SAMPLE_ISSUE}"
    })

    # TODO 4: Parse the JSON response and validate with your Pydantic model
    # Handle errors with try/except

    # TODO 5: Print each field on its own line

    await session.destroy()
    await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
