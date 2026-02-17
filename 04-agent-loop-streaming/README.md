# Chapter 04 — The Agent Loop & Streaming UX

![Chapter 04 banner illustration — a spinning loop with real-time text streaming out to a terminal](./images/banner.png)

<!-- TODO: Add banner image to ./04-agent-loop-streaming/images/banner.png — An illustration (1280×640) showing a circular agent reasoning loop with arrows connecting steps: "Read prompt" → "Think" → "Call tool" → "Get result" → "Think again" → "Respond". On the right side, a terminal shows lines of text appearing progressively (streaming effect). Same art style as course. -->

> **A great AI experience isn't just about the answer — it's about showing the thinking along the way.**

In the previous chapter, you added tools to your agent. When you called `send_and_wait`, the SDK silently ran the entire reasoning loop — thinking, calling tools, processing results — and only gave you the final answer. That works, but from the user's perspective the app freezes while thinking. This chapter teaches you how to show real-time progress with streaming and understand the agent loop that powers multi-step reasoning.

> ⚠️ **Prerequisites**: Make sure you've completed **[Chapter 03: Tool Calling](../03-tool-calling/README.md)** first. You'll need understanding of Python `async` / `await` and `pydantic` installed.

## 🎯 Learning Objectives

By the end of this chapter, you'll be able to:

- Explain how the agent reasoning loop works
- Enable streaming responses to show progressive output
- Listen for streaming events like `assistant.message_delta`
- Display tool usage progress in real time
- Set iteration limits to prevent infinite loops

> ⏱️ **Estimated Time**: ~45 minutes (15 min reading + 30 min hands-on)

---

# Understanding the Agent Loop

## 🧩 Real-World Analogy: The Open Kitchen

<img src="./images/analogy-open-kitchen.png" alt="Closed kitchen vs open kitchen comparison" width="800"/>

<!-- TODO: Add analogy image to ./04-agent-loop-streaming/images/analogy-open-kitchen.png — A split illustration: left side shows a frustrated diner staring at a blank wall (labeled "send_and_wait"); right side shows a happy diner watching a chef through an open kitchen window with live progress (labeled "Streaming"). Steps in the kitchen are labeled: "Read order → Select ingredients → Cook → Plate". Same art style as course. -->

Imagine two restaurants. At the first, you order and then stare at a blank wall for 20 minutes until a plate appears. At the second, there's an **open kitchen** — you can see the chef selecting ingredients, firing the grill, plating the dish. The food takes the same time, but the experience is completely different.

| Closed Kitchen (send_and_wait) | Open Kitchen (Streaming) |
|---|---|
| You wait in silence | You see each step as it happens |
| You wonder if something went wrong | You know exactly what's being prepared |
| You get the final dish all at once | You see ingredients, cooking, plating — then the dish |

Streaming turns your agent from a closed kitchen into an open one. The model is doing the same work either way — reasoning, calling tools, building a response — but with streaming, your user can watch each step unfold in real time.

The **agent loop** is the chef's process: read the order (prompt), decide what's needed (reasoning), grab an ingredient (tool call), check the result, decide if more is needed, and finally plate the dish (final response). Streaming lets you narrate that entire process to the user.

---

# Key Concepts

Let's understand the building blocks before diving into code.

---

## The Agent Reasoning Loop

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

---

## Preventing Infinite Loops

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

---

## Streaming Responses

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

---

## Listening for Streaming Events

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

---

## Tool Activity Events

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

# See It In Action

Let's build a streaming agent that shows real-time progress.

> 💡 **About Example Outputs**: The sample outputs shown throughout this course are illustrative. Because AI responses vary each time, your results will differ in wording, formatting, and detail.

## Building a Streaming Agent

Create a file called `streaming_agent.py`:

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

## Running the Demo

```bash
python streaming_agent.py
```

You should see output appearing progressively:

![Animated GIF showing streaming terminal output with tool calls and progressive text](./images/streaming-demo.gif)

<!-- TODO: Add animated GIF to ./04-agent-loop-streaming/images/streaming-demo.gif — Record a terminal session (80×24, ~15 seconds) running streaming_agent.py. Show: (1) "📋 Sending issue for review..." appears, (2) "🔧 Calling: get_file_contents..." appears, (3) "✅ Done: get_file_contents" appears, (4) A second tool call, (5) Response text streams in word by word, (6) "✅ Response complete." appears. Use a dark terminal theme. -->

<details>
<summary>🎬 See it in action!</summary>

![Streaming Demo](./images/streaming-demo.gif)

*Demo output varies. Your results will differ from what's shown here.*

</details>

## What's Happening Under the Hood

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

# Practice

<img src="../images/practice.png" alt="Warm desk setup ready for hands-on practice" width="800"/>

Time to put what you've learned into action.

---

## ▶️ Try It Yourself

After completing the demos above, try these experiments:

1. **Add timing information** — Modify the `on_delta` handler to print timestamps before each chunk

2. **Track iteration count** — Add a counter that increments each time a tool is called to see how many iterations the agent loop runs

3. **Custom progress messages** — Replace the emoji-based progress with a spinner or progress bar

4. **Session idle handling** — Register a `session.idle` handler that prints how long the entire process took

---

## 📝 Assignment

### Main Challenge: Add Streaming to Your Issue Reviewer

Extend your Issue Reviewer from Chapter 03 to show real-time progress:

1. Enable streaming in your session configuration with `"streaming": True`

2. Register event listeners for:
   - `assistant.message_delta` — print each chunk as it arrives
   - `tool.execution_start` — show which tool is being called
   - `tool.execution_complete` — confirm when tools finish

3. Build a `StatusReporter` class that tracks:
   - Total time elapsed
   - Number of tool calls
   - Final summary when complete

4. Handle the `session.idle` event for cleanup

**Success criteria**: Running your script shows real-time progress with tool calls and streaming text, then prints a summary when complete.

See [assignment.md](./assignment.md) for full instructions.

<details>
<summary>💡 Hints</summary>

**Enable streaming:**
```python
session = await client.create_session({
    "model": "gpt-4.1",
    "system_message": {"mode": "replace", "content": SYSTEM_PROMPT},
    "tools": [get_file_contents],
    "streaming": True  # ← Add this
})
```

**Common issues:**
- Forgetting `flush=True` in print statements — output appears delayed
- Not handling the case where no tools are called
- Mixing up `assistant.message` (final) with `assistant.message_delta` (chunks)

</details>

---

<details>
<summary>🔧 Common Mistakes & Troubleshooting</summary>

| Mistake | What Happens | Fix |
|---------|--------------|-----|
| Missing `flush=True` | Text appears in bursts instead of streaming | Add `flush=True` to print: `print(..., flush=True)` |
| Wrong event name | Handler never fires | Check exact event names: `assistant.message_delta`, not `message.delta` |
| Forgetting `end=""` | Each chunk on new line | Use `print(chunk, end="", flush=True)` |
| Not enabling streaming | No delta events fire | Add `"streaming": True` to session config |

### Knowledge Check

Test your understanding:

1. **What happens during each iteration of the agent loop?**
   - a) The model always calls exactly one tool
   - b) The model decides whether to call a tool or generate a response ✅
   - c) The model generates a response and then calls tools

2. **Which event fires for each chunk of streamed text?**
   - a) `assistant.message`
   - b) `assistant.message_delta` ✅
   - c) `session.text_chunk`

3. **How can you prevent the agent from calling tools indefinitely?**
   - a) Set `streaming: False`
   - b) Don't register any event listeners
   - c) Include explicit limits in the system prompt ✅

### Troubleshooting

**"No streaming output appears"** — Make sure `"streaming": True` is in your session config and you've registered the `assistant.message_delta` handler.

**"Text appears all at once"** — You're probably missing `flush=True` in your print statement. The output buffer needs to be flushed for real-time display.

**"Tool events never fire"** — The agent might not need to call tools for simple issues. Try an issue that references specific files.

</details>

---

# Summary

## 🔑 Key Takeaways

1. **The agent loop is multi-step** — the SDK orchestrates multiple iterations of reasoning, tool calling, and response generation automatically
2. **Streaming improves UX** — users see progress in real time instead of staring at a blank screen
3. **Events let you hook into the process** — `assistant.message_delta` for text chunks, `tool.execution_start/complete` for tool progress
4. **Session idle signals completion** — use `session.idle` to know when all processing is done

> 📚 **Glossary**: New to terms like "agent loop" or "streaming"? See the [Glossary](../GLOSSARY.md) for definitions.

---

## 🏗️ Capstone Progress

| Chapter | Feature Added | Status |
|---------|--------------|--------|
| 00 | Basic issue summary | ✅ |
| 01 | Structured output | ✅ |
| 02 | Reliable classification | ✅ |
| 03 | Tool calling (file fetch) | ✅ |
| **04** | **Streaming UX** | **🔲 ← You are here** |
| 05 | Concepts & mentoring | 🔲 |
| 06 | RAG for large repos | 🔲 |
| 07 | Safety & guardrails | 🔲 |
| 08 | Evaluation & testing | 🔲 |
| 09 | Production hardening | 🔲 |

---

## ➡️ What's Next

Your agent now shows real-time progress — but what if you want it to do more than just analyze issues?

In **[Chapter 05: Extracting Concepts & Mentoring Advice](../05-concepts-mentoring/README.md)**, you'll learn:

- How to extract skills and concepts from issues
- Generating personalized mentoring advice
- Building more sophisticated output schemas

You'll expand the Issue Reviewer to identify what skills are needed and provide learning recommendations.

---

## Additional Resources

- 📚 [GitHub Copilot SDK — Python streaming documentation](https://github.com/nicolo-ribaudo/copilot-sdk/tree/main/packages/sdk-python)
- 📚 [Event-driven patterns in asyncio](https://docs.python.org/3/library/asyncio.html)
- 📚 [Real-time UX best practices](https://www.nngroup.com/articles/response-times-3-important-limits/)

---

**[← Back to Chapter 03](../03-tool-calling/README.md)** | **[Continue to Chapter 05 →](../05-concepts-mentoring/README.md)**
