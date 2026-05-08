# Chapter 03 — Tool Calling: Giving the Agent Capabilities

<img src="./images/banner.png" alt="Illustration of an AI agent with extending tool arms holding files and connectors" style="max-width: 700px;">

> **An agent without tools is just a chatbot. Tools give your agent the ability to interact with the real world — reading files, calling APIs, and taking action.**

So far, your Issue Reviewer can analyze issue text that you paste into the prompt. But in the real world, issues often reference files. This chapter teaches you how to give your agent **tools** — the ability to fetch information and take actions on its own.

> ⚠️ **Prerequisites**: Make sure you've completed **[Chapter 02: Prompt Engineering](../02-prompt-engineering/README.md)** first. You'll need your rubric-based system prompt.

## 🎯 Learning Objectives

By the end of this chapter, you'll be able to:

- Explain what tools are in the context of AI agents
- Define custom tools using `@define_tool` and Pydantic models
- Understand the tool invocation lifecycle
- Give the agent the ability to read repository files

> ⏱️ **Estimated Time**: ~45 minutes (15 min reading + 30 min hands-on)

---

# Giving Your Agent Capabilities

## 🧩 Real-World Analogy: Giving the New Hire Building Access

<img src="./images/analogy-building-access.png" alt="Illustration of an employee using a key card to access a file room and retrieve information" style="max-width: 700px;">

Remember the employee you trained in Chapter 02? So far, they've been grading essays by reading only the cover sheet you hand them. If a student's essay says *"See appendix B for supporting data,"* your employee has to shrug — they can't go look at it.

Now imagine you give them a **key card** to the building's file room. When they encounter a reference, they can walk over, pull the file, read it, and come back with a much better analysis.

| Without Tools | With Tools |
|---|---|
| "The issue mentions `login.py` but I can't see it" | Agent reads `login.py` and includes the code in its analysis |
| Guesses based on the issue description alone | Makes informed judgments based on actual source code |
| Limited to what's in the prompt | Can invoke tools you've defined to fetch what it needs |

That's exactly what tools do. The `@define_tool` decorator is the key card — it gives the model permission and ability to access specific resources *that you decide to expose*. Based on your system prompt and tool descriptions, the SDK orchestrates when tools are called, and handles the back-and-forth execution.

---

# Key Concepts

Let's understand the core concepts behind tool calling.

**The pattern here — Plan → Fetch → Reason → Respond — is how every real-world AI agent with external data access works.**

<details>
<summary>🧭 Framework You Can Reuse Later: Plan -> Fetch -> Reason -> Respond (optional on first read)</summary>

If this is your first pass, you can skip this and come back after building the tool.

Tool calling generalizes into a reusable workflow:

1. Plan what information is needed
2. Fetch it through the minimum required tools
3. Reason over fetched results
4. Respond in a structured, constrained format

| Agent Type | Tool Workflow |
|---|---|
| Issue reviewer | read referenced files before scoring difficulty |
| Support bot | look up account context before replying |
| Ops assistant | query health metrics before recommending fixes |
| Release assistant | fetch changelog and test status before approval |

</details>

---

## What Are Tools?

A **tool** is a function you expose to the model that extends its capabilities beyond just generating text. Without tools, the model can only work with information you put directly in the prompt. With tools, you can configure the model to call APIs, query databases, read files, send notifications, or anything else you write as a Python function. **You decide which tools exist; the model can only use what you define.**

Each tool has:

1. **A name** — how the model refers to it (e.g., `get_weather`)
2. **A description** — signals to the model when this tool is appropriate (you write this)
3. **Parameters** — what arguments the tool accepts (defined as a schema)
4. **A handler** — the actual Python function that runs

> 💡 **You're the Architect**: Tools are how you give models capabilities. By defining a tool, you're deciding: "This operation is safe, needed, and I want the model to consider using it." Everything the model can do flows from decisions you made in code.

<img src="./images/tool-lifecycle.png" alt="Flowchart: Model sees tools, decides to call, SDK runs handler, result returned to model" style="max-width: 700px;">

Tools unlock a huge range of applications:

| Use Case | Tool Example |
|---|---|
| Customer support bot | `lookup_order(order_id)` — fetch order status from a database |
| DevOps assistant | `get_service_health(service_name)` — query a monitoring API |
| Research agent | `search_papers(query)` — search an academic database |
| Code reviewer | `get_file_contents(path)` — read source files from a repository |
| Travel planner | `check_flights(origin, dest, date)` — query a flights API |

The pattern is always the same: you define a function, describe what it does, and the model decides when to call it.

---

## The Tool Schema

Tools are defined using Pydantic models (for type-safe schemas) and the `@define_tool` decorator. Here's a simple example — a tool that fetches weather data:

```python
from pydantic import BaseModel, Field
from copilot import define_tool

class WeatherParams(BaseModel):
    city: str = Field(description="Name of the city to check weather for")

@define_tool(description="Get the current weather for a city")
async def get_weather(params: WeatherParams) -> str:
    # In a real tool, this would call a weather API
    return f"Weather in {params.city}: 72°F, sunny"
```

The structure is straightforward:
1. **Define a Pydantic model** with the parameters the tool needs
2. **Decorate the function** with `@define_tool` and a clear description
3. **Return a string** — the model will incorporate the result into its reasoning

This same pattern works for any tool. For the Issue Reviewer capstone, we'll create a file-reading tool — but the structure is identical whether you're reading files, calling APIs, or querying databases.

---

## How Tool Calling Is Orchestrated

When you provide tools and a prompt, the SDK orchestrates tool usage based on:

1. **Your system prompt** — which instructs the model to use tools for specific tasks
2. **Tool descriptions** — which you write to signal when each tool is appropriate
3. **The model's reasoning** — the model responds to your instructions and descriptions

The model can:
- **Call a tool** when your prompt directs it to gather information
- **Call multiple tools** in sequence for multi-step reasoning (as you've instructed)
- **Skip tools entirely** if your instructions indicate they're not needed

> 💡 **Developer Control**: You control the flow through your system prompt. Write clear, specific tool descriptions. Your prompt engineering determines how often and when tools are used.

> 🛡️ **Trust the Design**: The model follows your blueprint. If you've defined tools carefully and written clear instructions, the system will behave predictably.

---

# See It In Action

Let's create a tool that reads files from a local repository.

> 💡 **About Example Outputs**: The sample outputs shown throughout this course are illustrative. Because AI responses vary each time, your results will differ in wording, formatting, and detail.

## Defining a File Reader Tool

```python
import asyncio
import json
import os
from copilot import CopilotClient, define_tool
from copilot.session import PermissionHandler
from copilot.generated.session_events import AssistantMessageData
from pydantic import BaseModel, Field


class GetFileParams(BaseModel):
    file_path: str = Field(description="Relative path to the file in the repository")


# Define the tool — the model can call this when it needs file contents
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
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found: {params.file_path}"
    except Exception as e:
        return f"Error reading file: {e}"
```

<details>
<summary>🤖 Generate this with a prompt</summary>

Copy this prompt into GitHub Copilot Chat or your preferred AI assistant:

```text
Create a file-reading tool for the GitHub Copilot SDK. It should:
1. Define a GetFileParams Pydantic model with a file_path field (str)
2. Use @define_tool decorator with a description about reading repository files
3. The handler should:
   - Read REPO_PATH from an environment variable (default ".")
   - Join the repo root with the requested file path
   - Add path traversal protection using os.path.realpath() to ensure the
     resolved path stays within the repo root
   - Return "Access denied" if the path escapes the repo
   - Handle FileNotFoundError gracefully
   - Return the file contents as a string

Import os, and use copilot's define_tool and pydantic's BaseModel/Field.
```

</details>

---

## Using the Tool in a Session

Now let's pass the tool to a session and let the model use it:

```python
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

ISSUE_WITH_FILE_REFS = """
Title: Fix authentication bypass in login handler

The login handler in src/auth/login.py has a vulnerability where
expired JWT tokens are still accepted. The validate_token() function
in src/auth/tokens.py doesn't check the 'exp' claim properly.
"""


async def main():
    client = CopilotClient()
    await client.start()

    session = await client.create_session(
        on_permission_request=PermissionHandler.approve_all,
        model="gpt-4.1",
        system_message={"mode": "replace", "content": SYSTEM_PROMPT},
        tools=[get_file_contents],  # Pass your tool to the session
    )

    # The model will detect file references and call get_file_contents
    response = await session.send_and_wait(
        f"Analyze this issue:\n\n{ISSUE_WITH_FILE_REFS}"
    )

    if response and isinstance(response.data, AssistantMessageData):
        print(response.data.content)

    await session.disconnect()
    await client.stop()


asyncio.run(main())
```

<details>
<summary>🤖 Generate this with a prompt</summary>

Copy this prompt into GitHub Copilot Chat or your preferred AI assistant:

```text
Create a Python script using the GitHub Copilot SDK that passes a file-reading
tool to a session. It should:
1. Create a SYSTEM_PROMPT telling the model it's a GitHub issue analyzer with
   access to repository files, and to use get_file_contents when issues
   reference specific files. Output should be JSON with summary, difficulty_score,
   recommended_level, and files_analyzed fields.
2. Define a test issue about an authentication bypass that references
   src/auth/login.py and src/auth/tokens.py
3. Create a session with the system prompt (mode: replace) and pass the
   get_file_contents tool in the tools list
4. Send the issue and print the response

Use CopilotClient with async/await.
```

</details>

---

## Watching Tool Calls in Action

To see when the model calls your tool, register an event listener:

```python
from copilot.generated.session_events import ToolExecutionStartData, ToolExecutionCompleteData

def on_event(event):
    match event.data:
        case ToolExecutionStartData():
            print(f"🔧 Tool called: {event.data.tool_name}")
            print(f"   Arguments: {event.data.arguments}")
        case ToolExecutionCompleteData():
            print(f"✅ Tool complete")

session.on(on_event)
```

<details>
<summary>🤖 Generate this with a prompt</summary>

Copy this prompt into GitHub Copilot Chat or your preferred AI assistant:

```text
Create an event listener function for the GitHub Copilot SDK that logs tool calls.
The function should:
1. Import ToolExecutionStartData and ToolExecutionCompleteData from copilot.generated.session_events
2. Define an on_event(event) function that uses match/case on event.data:
   - case ToolExecutionStartData(): print the tool name and arguments with a wrench emoji
   - case ToolExecutionCompleteData(): print a checkmark confirmation
3. Register it with session.on(on_event)
```

</details>

---

## 📚 Extra Reading: Parallel Tool Calls

The model can sometimes call multiple tools in parallel for efficiency. For example, if an issue references three files, the model might request all three file reads simultaneously.

Things to consider:
- **Ordering** — if one tool depends on another's output, the model handles sequencing
- **Determinism** — parallel calls may return in different orders
- **Optional challenge:** Add a second tool, like `get_commit_history(file_path)`, and see how the model uses both together

---

# Practice

<img src="../images/practice.png" alt="Illustration of a desk setup ready for hands-on coding practice" style="max-width: 700px;">

Time to put what you've learned into action.

---

## ▶️ Try It Yourself

After completing the demo above, try these experiments:

1. **Add event listeners** — Implement the `on_event` function to watch tool calls in real-time

2. **Create a security test** — Try to make the agent read a file outside the repository (it should be blocked)

3. **Add a second tool** — Create `list_directory(path)` to list files in a folder

4. **Test tool selection** — Give an issue without file references and confirm the model skips the tool

---

## 📝 Assignment

### Main Challenge: Add File Reading to Your Issue Reviewer

Upgrade your Issue Reviewer with tool calling capabilities:

1. Add a `get_file_contents` tool that reads files from a local repository

2. Add **path validation** to prevent the model from accessing files outside the repo

3. Update your system prompt to tell the model about the new capability

4. Test with an issue that references specific files

**Success criteria**: The agent successfully reads referenced files and includes code context in its analysis.

See [assignment.md](./assignment.md) for full instructions.

<details>
<summary>💡 Hints</summary>

**Tool definition:**
```python
@define_tool(description="Read the contents of a file from the repository")
async def get_file_contents(params: GetFileParams) -> str:
    ...
```

**Path validation:**
```python
full_path = os.path.realpath(full_path)
if not full_path.startswith(os.path.realpath(repo_root)):
    return "Error: Access denied"
```

**Common issues:**
- Forgot to add the tool to `tools` list in session config
- Tool description too vague — model doesn't know when to use it
- Missing error handling for files that don't exist

</details>

---

<details>
<summary>🔧 Common Mistakes & Troubleshooting</summary>

| Mistake | What Happens | Fix |
|---------|--------------|-----|
| Forgot to add tool to session | Model can't see or use the tool | Add `tools: [get_file_contents]` to session config |
| Vague tool description | Model doesn't know when to use it | Be specific: "Read the contents of a file from the repository" |
| No path validation | Security vulnerability — model can read any file | Validate paths stay within repo root |
| No error handling | Crashes on missing files | Return error messages instead of raising exceptions |

### Troubleshooting

**Tool never called** — Check your system prompt. Does it mention the tool? Does the issue reference files?

**"Access denied" errors** — Your path validation may be too strict. Make sure you're using `os.path.realpath()` on both paths.

**Model reads wrong file** — The model is guessing the path. Add better context in the issue or prompt.

</details>

---

## 🧠 Knowledge Check

Test your understanding:

1. **What are tools in the context of the Copilot SDK?**
   - a) IDE plugins that help you write code
   - b) Functions you define that the model can invoke to fetch data or perform actions ✅
   - c) Built-in SDK commands for debugging

2. **Who decides when to call a tool during a conversation?**
   - a) You, the developer, by calling the tool explicitly
   - b) The SDK framework, on a fixed schedule
   - c) The model, based on whether the tool would help answer the query ✅

3. **Why is path validation critical for a file-reading tool?**
   - a) To make the tool run faster
   - b) To prevent the model from reading sensitive files outside the allowed directory ✅
   - c) To ensure the file exists before reading

---

# Wrap-Up

## ✅ What You Can Do Now

1. **Tools extend agent capabilities** — they let the agent fetch information and take actions beyond text generation
2. **The model decides when to call tools** — you define them, the model chooses when they're needed
3. **Security is critical** — always validate inputs and restrict access to authorized resources only
4. **Clear descriptions matter** — the model uses tool descriptions to decide when a tool is appropriate

> 📚 **Glossary**: New to terms like "tool" or "hook"? See the [Glossary](../GLOSSARY.md) for definitions.

---

<details>
<summary>📦 Optional: Progress and reference</summary>

## 🏗️ Capstone Progress

| Chapter | Feature Added | Status |
|---------|--------------|--------|
| 00 | Basic issue summary | ✅ |
| 01 | Structured output with rich fields | ✅ |
| 02 | Reliable classification | ✅ |
| **03** | **Tool calling (file fetch)** | **🔲 ← You are here** |
| 04 | Streaming UX | 🔲 |
| 05 | Safety & guardrails | 🔲 |
| 06 | Production & GitHub integration | 🔲 |

> ✅ **Milestone: Working Prototype** — After completing this chapter, your Issue Reviewer can analyze issues, produce structured output, classify consistently, and read referenced files. You have a fully functional local prototype! The next three chapters focus on polish, safety, and production readiness.

**Your task:** Add a `get_file_contents` tool so the Issue Reviewer can read referenced files.

See [assignment.md](./assignment.md) for full instructions.

---

## ▶️ Next Step

Your agent can now fetch files — but what if it needs multiple steps of reasoning? In **[Chapter 04: Agent Loop & Streaming](../04-agent-loop-streaming/README.md)**, you'll learn:

- How the agent loop enables multi-step reasoning
- Streaming responses for better UX
- Handling complex tasks that require multiple tool calls

You'll upgrade your Issue Reviewer to provide real-time progress updates.

---

## 📚 Additional Resources

> 📚 **Official Documentation**: [GitHub Copilot SDK](https://github.com/github/copilot-sdk) — full API reference and guides
>
> 📋 **Quick Reference**: [Python SDK README](https://github.com/github/copilot-sdk/blob/main/python/README.md) — setup, configuration, and examples

- 📚 [Copilot SDK — Tools](https://github.com/github/copilot-sdk/blob/main/python/README.md#tools)
- 📚 [Pydantic Models](https://docs.pydantic.dev/latest/concepts/models/)

## Ship-Readiness Checklist

- [ ] Tool descriptions are clear and action-specific
- [ ] Tool inputs are validated before execution
- [ ] File and path access are scoped to allowed directories
- [ ] Tool failures return safe, explicit error messages
- [ ] Final response remains structured and deterministic

</details>

---

**[← Back to Chapter 02](../02-prompt-engineering/README.md)** | **[Continue to Chapter 04 →](../04-agent-loop-streaming/README.md)**
