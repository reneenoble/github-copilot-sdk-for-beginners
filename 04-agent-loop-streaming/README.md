# Chapter 4 — The Agent Loop & Streaming UX

![Chapter 4 banner illustration — a spinning loop with real-time text streaming out to a terminal](./images/banner.png)

<!-- TODO: Add banner image to ./04-agent-loop-streaming/images/banner.png — An illustration (1280×640) showing a circular agent reasoning loop with arrows connecting steps: "Read prompt" → "Think" → "Call tool" → "Get result" → "Think again" → "Respond". On the right side, a terminal shows lines of text appearing progressively (streaming effect). Same art style as course. -->

> *"A great AI experience isn't just about the answer — it's about showing the thinking along the way."*

## What You'll Learn

After this lesson, you will be able to:

- ✅ Explain how the agent reasoning loop works
- ✅ Enable streaming responses to show progressive output
- ✅ Listen for streaming events like `assistant.message_delta`
- ✅ Display tool usage progress in real time
- ✅ Set iteration limits to prevent infinite loops

## Pre-requisites

- Completed [Chapter 3 — Tool Calling](../03-tool-calling/README.md)
- Understanding of Python `async` / `await`

---

## Introduction

In the previous chapter, you added tools to your agent. When you called `send_and_wait`, the SDK silently ran the entire reasoning loop — thinking, calling tools, processing results — and only gave you the final answer. That works, but from the user's perspective the app freezes while thinking.

In production, users want to see **progress**. They want to know the agent is working, what it's doing, and how it's progressing. That's where **streaming** comes in.

This chapter covers two important concepts:

1. **The Agent Loop** — how the SDK orchestrates multi-step reasoning
2. **Streaming** — how to show real-time updates as the agent works

---

## Key Concepts

### The Agent Reasoning Loop

When you call `send_and_wait`, the SDK doesn't just make a single API call. It runs a **loop**:

![Agent loop diagram — a flowchart showing the multi-step reasoning cycle](./images/agent-loop-diagram.png)

<!-- TODO: Add diagram to ./04-agent-loop-streaming/images/agent-loop-diagram.png — A flowchart (800×600) showing: (1) "User sends prompt" → (2) "Model thinks" → Decision diamond: "Need a tool?" → YES → (3) "Call tool" → (4) "Get result" → back to (2). NO → (5) "Generate response" → (6) "Return to user". Add a counter label showing "Iteration 1, 2, 3..." on the loop back arrow. Include a red "Max iterations" guard on the loop. -->

Here's what happens in each iteration:

1. **The model receives** the conversation so far (system prompt + messages + tool results)
2. **The model decides** whether to call a tool or generate a response
3. **If it calls a tool**, the SDK runs your handler and feeds the result back
4. **If it generates a response**, the loop ends and the result is returned

This loop can run multiple iterations. For example, your Issue Reviewer might:

- **Iteration 1**: Read the issue, decide to fetch `src/auth/login.py`
- **Iteration 2**: Read the file contents, decide to also fetch `src/auth/tokens.py`
- **Iteration 3**: Analyze both files and generate the final review

### Preventing Infinite Loops

What if the model keeps calling tools forever? The SDK includes a default iteration limit, but you should also be aware of it in your design:

```python
# The agent will stop after a reasonable number of iterations
# If you need to adjust behavior, design your prompts carefully
session = await client.create_session({
    "model": "gpt-4.1",
    "system_message": {
        "mode": "replace",
        "content": """Analyze the issue and respond with your assessment.
        
IMPORTANT: Read at most 3 files. If an issue references more than 3 files,
analyze the first 3 and note the others in your response."""
    },
    "tools": [get_file_contents]
})
```

> 💡 **Tip**: Limiting tool usage in the system prompt is a practical way to keep the agent focused and prevent excessive iteration.

### Streaming Responses

Instead of waiting for the complete response, you can **stream** it — receiving text as the model generates it, word by word. Enable streaming in your session configuration:

```python
session = await client.create_session({
    "model": "gpt-4.1",
    "system_message": {
        "mode": "replace",
        "content": "You are a GitHub issue reviewer."
    },
    "tools": [get_file_contents],
    "streaming": True  # ← Enable streaming
})
```

### Listening for Streaming Events

With streaming enabled, you can hook into events as they happen:

```python
# Stream text as it arrives
def on_delta(event):
    print(event.data.delta_content, end="", flush=True)

session.on("assistant.message_delta", on_delta)

# Know when the final message is complete
def on_complete(event):
    print("\n\n--- Response complete ---")

session.on("assistant.message", on_complete)
```

### Tool Activity Events

You can also listen for tool-related events to show progress:

```python
def on_tool_start(event):
    print(f"\n🔧 Calling tool: {event.data.tool_name}...")

def on_tool_complete(event):
    print(f"✅ Tool complete: {event.data.tool_name}")

session.on("tool.execution_start", on_tool_start)
session.on("tool.execution_complete", on_tool_complete)
```

Combining these events, you can build an experience like:

```
🔧 Calling tool: get_file_contents...
✅ Tool complete: get_file_contents
🔧 Calling tool: get_file_contents...
✅ Tool complete: get_file_contents

Based on my analysis of the issue and the referenced files...
The authentication bypass in login.py occurs because...
```

---

## Demo Walkthrough

Let's build a streaming agent that shows real-time progress. Create a file called `streaming_agent.py`:

```python
import asyncio
from copilot import CopilotClient, define_tool
from pydantic import BaseModel, Field
import os


class GetFileParams(BaseModel):
    file_path: str = Field(description="Relative path to the file")


@define_tool(description="Read the contents of a file from the repository")
async def get_file_contents(params: GetFileParams) -> str:
    repo_root = os.environ.get("REPO_PATH", ".")
    full_path = os.path.realpath(os.path.join(repo_root, params.file_path))
    if not full_path.startswith(os.path.realpath(repo_root)):
        return "Error: Access denied"
    try:
        with open(full_path, "r") as f:
            content = f.read()
            return content[:10_000] if len(content) > 10_000 else content
    except FileNotFoundError:
        return f"Error: File not found: {params.file_path}"


async def main():
    client = CopilotClient()
    await client.start()

    session = await client.create_session({
        "model": "gpt-4.1",
        "system_message": {
            "mode": "replace",
            "content": """You are a GitHub issue reviewer. Analyze the issue,
fetch any referenced files, and provide a detailed assessment.

Respond in plain text with clear sections:
- Summary
- Files analyzed
- Assessment"""
        },
        "tools": [get_file_contents],
        "streaming": True
    })

    # --- Register event listeners ---
    def on_delta(event):
        """Print each chunk of text as it arrives."""
        print(event.data.delta_content, end="", flush=True)

    def on_message(event):
        """Called when the full message is assembled."""
        print("\n\n✅ Response complete.")

    def on_tool_start(event):
        """Show which tool is being called."""
        print(f"\n🔧 Calling: {event.data.tool_name}...")

    def on_tool_complete(event):
        """Confirm tool execution finished."""
        print(f"✅ Done: {event.data.tool_name}\n")

    session.on("assistant.message_delta", on_delta)
    session.on("assistant.message", on_message)
    session.on("tool.execution_start", on_tool_start)
    session.on("tool.execution_complete", on_tool_complete)

    # --- Send the issue ---
    issue = """
    Title: Fix token expiry validation

    The validate_token() function in src/auth/tokens.py doesn't check the
    'exp' claim. Expired tokens are accepted by the login handler in
    src/auth/login.py. This is a security vulnerability.
    """

    print("📋 Sending issue for review...\n")
    response = await session.send_and_wait({"prompt": issue})

    await client.stop()


asyncio.run(main())
```

### Running the Demo

```bash
python streaming_agent.py
```

You should see output appearing progressively:

![Animated GIF showing streaming terminal output with tool calls and progressive text](./images/streaming-demo.gif)

<!-- TODO: Add animated GIF to ./04-agent-loop-streaming/images/streaming-demo.gif — Record a terminal session (80×24, ~15 seconds) running streaming_agent.py. Show: (1) "📋 Sending issue for review..." appears, (2) "🔧 Calling: get_file_contents..." appears, (3) "✅ Done: get_file_contents" appears, (4) A second tool call, (5) Response text streams in word by word, (6) "✅ Response complete." appears. Use a dark terminal theme. -->

### What's Happening Under the Hood

When you run this:

1. `send_and_wait` starts the agent loop
2. The model reads the issue and decides to call `get_file_contents` for `src/auth/tokens.py`
3. The `tool.execution_start` event fires — you see "🔧 Calling..."
4. Your tool handler runs and returns the file content
5. The `tool.execution_complete` event fires — you see "✅ Done"
6. The model may call another tool (loop continues)
7. When the model generates its response, `assistant.message_delta` fires for each chunk
8. When complete, `assistant.message` fires once

---

## Session Idle — Knowing When Everything Is Done

The `session.idle` event fires when the session has fully finished processing — all tool calls are done, all messages streamed, and no more work is pending:

```python
def on_idle(event):
    print("\n🏁 Session is idle — all processing complete.")

session.on("session.idle", on_idle)
```

This is useful when you need to perform cleanup or trigger downstream actions after the agent finishes.

---

## Building a Status Reporter

Here's a practical pattern — a status reporter that tracks the agent's progress through labeled phases:

```python
import time

class StatusReporter:
    def __init__(self):
        self.start_time = time.time()
        self.tools_called = 0

    def elapsed(self):
        return f"{time.time() - self.start_time:.1f}s"

    def on_tool_start(self, event):
        self.tools_called += 1
        print(f"  [{self.elapsed()}] 🔧 Tool #{self.tools_called}: "
              f"{event.data.tool_name}")

    def on_tool_complete(self, event):
        print(f"  [{self.elapsed()}] ✅ Complete")

    def on_delta(self, event):
        print(event.data.delta_content, end="", flush=True)

    def on_complete(self, event):
        print(f"\n\n📊 Finished in {self.elapsed()} "
              f"with {self.tools_called} tool call(s)")

    def register(self, session):
        session.on("tool.execution_start", self.on_tool_start)
        session.on("tool.execution_complete", self.on_tool_complete)
        session.on("assistant.message_delta", self.on_delta)
        session.on("assistant.message", self.on_complete)
```

Usage:

```python
status = StatusReporter()
status.register(session)
```

---

## Knowledge Check ✅

Test your understanding with these questions:

1. **What happens during each iteration of the agent loop?**
   - a) The model always calls exactly one tool
   - b) The model decides whether to call a tool or generate a response
   - c) The model generates a response and then calls tools
   - d) The SDK randomly selects a tool to call

2. **Which event fires for each chunk of streamed text?**
   - a) `assistant.message`
   - b) `assistant.message_delta`
   - c) `assistant.streaming`
   - d) `session.text_chunk`

3. **How can you prevent the agent from calling tools indefinitely?**
   - a) Set `streaming: False`
   - b) Don't register any event listeners
   - c) Include explicit limits in the system prompt
   - d) Use `send` instead of `send_and_wait`

<details>
<summary>Answers</summary>

1. **b** — The model decides whether to call a tool or generate a response in each iteration.
2. **b** — `assistant.message_delta` fires for each chunk of streamed response text.
3. **c** — Including explicit limits in the system prompt (e.g., "read at most 3 files") is a practical way to prevent excessive tool calls.

</details>

---

## Capstone Progress 🏗️

Your Issue Reviewer now has streaming! Here's what you've built so far:

| Chapter | Feature | Status |
|---------|---------|--------|
| 0 | Basic SDK setup & issue summarization | ✅ |
| 1 | Structured JSON output with Pydantic validation | ✅ |
| 2 | Reliable classification with prompt engineering | ✅ |
| 3 | Tool calling for file access | ✅ |
| **4** | **Streaming UX & agent loop awareness** | **✅ New!** |
| 5 | Concept extraction & mentoring advice | ⬜ |
| 6 | RAG for large repositories | ⬜ |
| 7 | Safety & guardrails | ⬜ |
| 8 | Evaluation & testing | ⬜ |
| 9 | Production hardening & GitHub integration | ⬜ |

## Next Step

In [Chapter 5 — Extracting Concepts & Mentoring Advice](../05-concepts-mentoring/README.md), you'll expand the reviewer to identify required skills and generate personalized mentoring advice based on the issue's difficulty level.

---

## Additional Resources

- [GitHub Copilot SDK — Python streaming documentation](https://github.com/nicolo-ribaudo/copilot-sdk/tree/main/packages/sdk-python)
- [Event-driven patterns in asyncio](https://docs.python.org/3/library/asyncio.html)
