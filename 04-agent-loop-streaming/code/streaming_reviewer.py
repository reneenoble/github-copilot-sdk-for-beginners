"""
Chapter 4 — The Agent Loop & Streaming UX: Starter Code
GitHub Copilot SDK for Beginners

Add streaming to the Issue Reviewer so it shows real-time progress.
"""

import asyncio
import json
import os
import time
from copilot import CopilotClient, define_tool
from pydantic import BaseModel, Field


# --- Tool Definition (from Chapter 3) ---

class GetFileParams(BaseModel):
    file_path: str = Field(description="Relative path to the file in the repository")


@define_tool(description="Read the contents of a file from the repository")
async def get_file_contents(params: GetFileParams) -> str:
    repo_root = os.environ.get("REPO_PATH", ".")
    full_path = os.path.realpath(os.path.join(repo_root, params.file_path))
    if not full_path.startswith(os.path.realpath(repo_root)):
        return "Error: Access denied — path is outside the repository"
    try:
        with open(full_path, "r") as f:
            content = f.read()
            return content[:10_000] if len(content) > 10_000 else content
    except FileNotFoundError:
        return f"Error: File not found: {params.file_path}"


# --- Status Reporter ---

# TODO 1: Create a StatusReporter class with:
#   - __init__: store start time (time.time()) and tool counter (0)
#   - elapsed(): return formatted elapsed time string like "1.2s"
#   - on_tool_start(event): increment counter, print tool name with timestamp
#   - on_tool_complete(event): print completion with timestamp
#   - on_delta(event): print event.data.delta_content with end="" and flush=True
#   - on_complete(event): print summary with elapsed time and tool count
#   - register(session): register all event listeners on the session


SYSTEM_PROMPT = """You are a GitHub issue reviewer. Analyze the issue,
fetch any referenced files using the get_file_contents tool, and provide
a structured assessment.

Read at most 3 files. If more are referenced, note them but skip.

Respond in plain text with sections:
- Summary
- Files Analyzed
- Difficulty Assessment (1-5)
- Key Findings"""


SAMPLE_ISSUE = """
Title: Fix authentication bypass in login handler

The login handler in src/auth/login.py has a vulnerability where
expired JWT tokens are still accepted. The validate_token() function
in src/auth/tokens.py doesn't check the 'exp' claim properly.

Additionally, the session management in src/auth/sessions.py may need
to be updated to invalidate sessions with expired tokens.
"""


async def main():
    client = CopilotClient()
    await client.start()

    # TODO 2: Create a session with streaming enabled.
    # Include the system prompt, tools, and set streaming to True.
    session = await client.create_session({
        "model": "gpt-4.1",
        "system_message": {
            "mode": "replace",
            "content": SYSTEM_PROMPT
        },
        "tools": [get_file_contents],
        # Add streaming configuration here
    })

    # TODO 3: Create a StatusReporter instance and register it with the session.

    # TODO 4: Send the issue and observe the streaming output.
    print("📋 Sending issue for review...\n")
    response = await session.send_and_wait({"prompt": SAMPLE_ISSUE})

    await client.stop()


asyncio.run(main())
