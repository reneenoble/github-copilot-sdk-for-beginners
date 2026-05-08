"""
Chapter 4 — The Agent Loop & Streaming UX: Solution
GitHub Copilot SDK for Beginners

Issue Reviewer with streaming output and a StatusReporter for real-time progress.
"""

import asyncio
import json
import os
import time
from copilot import CopilotClient, define_tool
from copilot.session import PermissionHandler
from copilot.generated.session_events import (
    AssistantMessageData,
    AssistantMessageDeltaData,
    SessionIdleData,
    ToolExecutionStartData,
    ToolExecutionCompleteData,
)
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

class StatusReporter:
    """Tracks agent progress and prints real-time status updates."""

    def __init__(self):
        self.start_time = time.time()
        self.tools_called = 0
        self.chars_received = 0
        self._tool_names: dict[str, str] = {}  # tool_call_id → tool_name

    def elapsed(self) -> str:
        return f"{time.time() - self.start_time:.1f}s"

    def on_tool_start(self, event):
        self.tools_called += 1
        self._tool_names[event.data.tool_call_id] = event.data.tool_name
        print(f"  [{self.elapsed()}] 🔧 Tool #{self.tools_called}: "
              f"{event.data.tool_name}")

    def on_tool_complete(self, event):
        name = self._tool_names.get(event.data.tool_call_id, "unknown")
        print(f"  [{self.elapsed()}] ✅ Complete: {name}")

    def on_delta(self, event):
        chunk = event.data.delta_content
        self.chars_received += len(chunk)
        print(chunk, end="", flush=True)

    def on_complete(self, event):
        print(f"\n\n{'─' * 50}")
        print(f"📊 Finished in {self.elapsed()}")
        print(f"   Tool calls: {self.tools_called}")
        print(f"   Characters streamed: {self.chars_received}")
        print(f"{'─' * 50}")

    def on_idle(self, event):
        print(f"\n🏁 Session idle — all processing complete ({self.elapsed()})")

    def register(self, session):
        """Register all event listeners on the session."""
        def on_event(event):
            match event.data:
                case ToolExecutionStartData():
                    self.on_tool_start(event)
                case ToolExecutionCompleteData():
                    self.on_tool_complete(event)
                case AssistantMessageDeltaData():
                    self.on_delta(event)
                case AssistantMessageData():
                    self.on_complete(event)
                case SessionIdleData():
                    self.on_idle(event)

        session.on(on_event)


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

    # Create session with streaming enabled
    session = await client.create_session(
        on_permission_request=PermissionHandler.approve_all,
        model="gpt-4.1",
        system_message={
            "mode": "replace",
            "content": SYSTEM_PROMPT
        },
        tools=[get_file_contents],
        streaming=True,
    )

    # Create and register the status reporter
    status = StatusReporter()
    status.register(session)

    # Send the issue — streaming events will fire automatically
    print("📋 Sending issue for review...\n")
    await session.send_and_wait(SAMPLE_ISSUE)

    await client.stop()


asyncio.run(main())
