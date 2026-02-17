"""
Chapter 3 — Tool Calling: Solution
GitHub Copilot SDK for Beginners

Issue Reviewer with a get_file_contents tool for reading repository files.
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


class GetFileParams(BaseModel):
    file_path: str = Field(description="Relative path to the file in the repository")


@define_tool(description="Read the contents of a file from the repository")
async def get_file_contents(params: GetFileParams) -> str:
    """Read a file from the local repository."""
    repo_root = os.environ.get("REPO_PATH", ".")
    full_path = os.path.join(repo_root, params.file_path)

    # Safety: prevent path traversal
    full_path = os.path.realpath(full_path)
    if not full_path.startswith(os.path.realpath(repo_root)):
        return "Error: Access denied — path is outside the repository"

    try:
        with open(full_path, "r") as f:
            content = f.read()
            # Limit content to avoid overwhelming the context
            if len(content) > 10_000:
                return content[:10_000] + "\n\n... [truncated — file too large]"
            return content
    except FileNotFoundError:
        return f"Error: File not found: {params.file_path}"
    except Exception as e:
        return f"Error reading file: {e}"


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

## Difficulty Rubric
Score 1 — Junior: Typos, docs, config. No logic changes.
Score 2 — Junior/Mid: Simple bug, single file.
Score 3 — Mid: Feature in one subsystem, 2-5 files.
Score 4 — Senior: Cross-cutting (perf, security). Multiple subsystems.
Score 5 — Senior+: Architecture redesign, migration.
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

    session = await client.create_session({
        "model": "gpt-4.1",
        "system_message": {"mode": "replace", "content": SYSTEM_PROMPT},
        "tools": [get_file_contents],
    })

    # Log tool calls
    def on_event(event):
        if event.type.value == "tool.execution_start":
            print(f"🔧 Tool called: {event.data.tool_name}")
        elif event.type.value == "tool.execution_complete":
            print(f"✅ Tool complete: {event.data.tool_name}")

    session.on(on_event)

    response = await session.send_and_wait({
        "prompt": f"Analyze this issue:\n\n{SAMPLE_ISSUE}"
    })

    print("\n--- Analysis Result ---")
    try:
        data = json.loads(response.data.content)
        analysis = IssueAnalysis(**data)
        print(f"Summary:    {analysis.summary}")
        print(f"Difficulty: {analysis.difficulty_score}/5")
        print(f"Level:      {analysis.recommended_level}")
        print(f"Files:      {', '.join(analysis.files_analyzed)}")
    except Exception as e:
        print(f"Error: {e}")
        print(f"Raw: {response.data.content}")

    await session.destroy()
    await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
