"""
Chapter 3 — Tool Calling: Starter Code
GitHub Copilot SDK for Beginners

TODO: Define a get_file_contents tool and integrate it with the Issue Reviewer.
"""

import asyncio
import json
import os
from copilot import CopilotClient, define_tool
from pydantic import BaseModel, Field


class IssueAnalysis(BaseModel):
    summary: str
    difficulty_score: int = Field(ge=1, le=5)
    recommended_level: str
    files_analyzed: list[str] = Field(default_factory=list)


# TODO 1: Define a Pydantic model for the tool parameters
# class GetFileParams(BaseModel):
#     file_path: str = Field(description="...")


# TODO 2: Define the get_file_contents tool using @define_tool
# Include path traversal protection!
# @define_tool(description="...")
# async def get_file_contents(params: GetFileParams) -> str:
#     ...


SYSTEM_PROMPT = """You are a GitHub issue analyzer with access to repository files.

When an issue references specific files, use the get_file_contents tool to read
those files and include code context in your analysis.

Respond with ONLY a JSON object:
{
  "summary": "<one sentence>",
  "difficulty_score": 1-5,
  "recommended_level": "Junior | Mid | Senior | Senior+",
  "files_analyzed": ["<list of files you read>"]
}
"""

SAMPLE_ISSUE = """
Title: Fix authentication bypass in login handler

The login handler in src/auth/login.py has a vulnerability where
expired JWT tokens are still accepted. The validate_token() function
in src/auth/tokens.py doesn't check the 'exp' claim properly.
"""


async def main():
    client = CopilotClient()
    await client.start()

    # TODO 3: Create session with the tool
    session = await client.create_session({
        "model": "gpt-4.1",
        "system_message": {"mode": "replace", "content": SYSTEM_PROMPT},
        # "tools": [get_file_contents],  # Uncomment after defining the tool
    })

    # TODO 4: Add event listener for tool calls
    # def on_event(event):
    #     if event.type.value == "tool.execution_start":
    #         print(f"🔧 Tool called: {event.data.tool_name}")
    # session.on(on_event)

    response = await session.send_and_wait({
        "prompt": f"Analyze this issue:\n\n{SAMPLE_ISSUE}"
    })

    try:
        data = json.loads(response.data.content)
        analysis = IssueAnalysis(**data)
        print(f"Summary:    {analysis.summary}")
        print(f"Difficulty: {analysis.difficulty_score}/5")
        print(f"Level:      {analysis.recommended_level}")
        print(f"Files:      {analysis.files_analyzed}")
    except Exception as e:
        print(f"Error: {e}")
        print(f"Raw: {response.data.content}")

    await session.destroy()
    await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
